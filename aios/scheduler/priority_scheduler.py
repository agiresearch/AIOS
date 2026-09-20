"""Priority-based LLM request scheduling for the AIOS kernel.

Why this exists
---------------
AIOS ships two LLM scheduling policies: ``FIFOScheduler`` (batched,
first-come-first-served) and ``RRScheduler`` (fixed time slice). Neither can
express *which agent matters more*, and neither protects an agent from being
crowded out.

Every syscall already carries a ``priority`` field
(``aios/syscall/__init__.py``) and the scheduler config section in
``aios/config/config.yaml.example`` has a single key, so the design clearly
anticipated a policy decision that was never implemented. ``PriorityScheduler``
implements it:

* the ready LLM syscall with the best **effective priority** is dispatched next,
* a request's effective priority improves the longer it waits (**aging**), so a
  LOW agent cannot be starved by a stream of HIGH requests,
* ties are broken by arrival time, then by arrival order, so dispatch is
  deterministic.

The policy itself lives in ``aios/scheduler/priority_policy.py`` and has no
AIOS imports; this module is the adapter that connects it to the kernel's
threads, queues and syscall lifecycle.

Scope
-----
Only the LLM path is priority-scheduled. Memory, storage and tool requests are
dispatched in arrival order, exactly as ``FIFOScheduler`` does, so the change
is confined to the decision this feature is about. The dispatcher does not
preempt a request that is already executing (AIOS's LLM calls are not
interruptible in the current design) -- priority orders *queued* requests.

Nothing existing is modified: ``FIFOScheduler`` and ``RRScheduler`` are
untouched and this policy is only used when explicitly selected.

Integration
-----------
Selected by name from ``config.yaml`` through ``aios.scheduler.registry``::

    scheduler:
      policy: "priority"
      priority:
        aging_interval: 5
        default_priority: "normal"
"""

from __future__ import annotations

import logging
import time
import traceback
from queue import Empty
from threading import Lock
from typing import Any, Dict, List, Optional

from .base import BaseScheduler
from .priority_policy import PendingRequest, PriorityLevel, PriorityPolicy
from .registry import POLICY_PRIORITY

logger = logging.getLogger(__name__)

#: Registry key for this policy (``scheduler.policy: priority`` in config).
POLICY_NAME = POLICY_PRIORITY


class PriorityScheduler(BaseScheduler):
    """Schedules LLM syscalls by effective priority, with aging.

    Example:
        ```python
        scheduler = PriorityScheduler(
            llm=llm_adapter,
            memory_manager=memory_mgr,
            storage_manager=storage_mgr,
            tool_manager=tool_mgr,
            log_mode="console",
            get_llm_syscall=llm_queue.get,
            get_memory_syscall=memory_queue.get,
            get_storage_syscall=storage_queue.get,
            get_tool_syscall=tool_queue.get,
            aging_interval=5,
        )
        scheduler.start()
        ```
    """

    def __init__(
        self,
        llm: Any,
        memory_manager: Any,
        storage_manager: Any,
        tool_manager: Any,
        log_mode: str,
        get_llm_syscall: Any,
        get_memory_syscall: Any,
        get_storage_syscall: Any,
        get_tool_syscall: Any,
        aging_interval: int = 5,
        default_priority: Any = PriorityLevel.NORMAL,
    ):
        """Initialise the priority scheduler.

        Args:
            llm: LLM adapter instance.
            memory_manager: Memory management instance.
            storage_manager: Storage management instance.
            tool_manager: Tool management instance.
            log_mode: Logging mode configuration.
            get_llm_syscall: Function to get LLM syscalls.
            get_memory_syscall: Function to get Memory syscalls.
            get_storage_syscall: Function to get Storage syscalls.
            get_tool_syscall: Function to get Tool syscalls.
            aging_interval: Dispatch rounds a waiting request needs to gain one
                priority level. Must be >= 1.
            default_priority: Level assumed when a syscall carries no priority.
        """
        super().__init__(
            llm,
            memory_manager,
            storage_manager,
            tool_manager,
            log_mode,
            get_llm_syscall,
            get_memory_syscall,
            get_storage_syscall,
            get_tool_syscall,
        )
        self.policy = PriorityPolicy(
            aging_interval=aging_interval,
            default_priority=default_priority,
        )

        # Ready set of admitted LLM syscalls, and the bookkeeping that gives the
        # policy a stable notion of "now". The lock guards the ready set and the
        # tick counter only -- never a dispatch, which may take minutes.
        self._ready: List[PendingRequest] = []
        self._ready_lock = Lock()
        self._sequence = 0
        self._tick = 0
        self._dispatched = 0

    # ------------------------------------------------------------------
    # Live observability
    # ------------------------------------------------------------------
    def _log_event(self, tag: str, message: str, level: str = "info") -> None:
        """Write one live allocation line to the scheduler log.

        Format: ``TAG      HH:MM:SS  message``. Every scheduling decision emits
        one of these, so a running kernel shows the ready set being ordered in
        real time, without a debugger or a metrics endpoint.
        """
        self.logger.log(
            f"{tag:<8} {time.strftime('%H:%M:%S')}  {message}\n",
            level,
        )

    def _label(self, request: PendingRequest) -> str:
        """Return the caller-facing priority name of a request."""
        return PriorityLevel.from_value(
            request.priority, self.policy.default_priority
        ).name.lower()

    def _log_ready_set(self) -> None:
        """Log the requests still waiting, in the order they will be dispatched.

        This is the line that makes the policy visible: after each dispatch the
        remaining queue is printed already sorted, with the aged level of every
        request, so a LOW request climbing to the front can be watched.
        """
        rows = self.ready_snapshot()
        if not rows:
            return
        rendered = ", ".join(
            f"{row['payload'].agent_name}"
            f"({PriorityLevel(row['effective_level']).name.lower()}"
            f",waited {row['wait_ticks']})"
            for row in rows
        )
        self._log_event("READY", f"next -> {rendered}")

    # ------------------------------------------------------------------
    # LLM path: priority-scheduled
    # ------------------------------------------------------------------
    def _admit(self, syscall: Any) -> PendingRequest:
        """Wrap a freshly queued syscall as a :class:`PendingRequest`."""
        request = PendingRequest(
            payload=syscall,
            priority=syscall.get_priority(),
            arrival_tick=self._tick,
            sequence=self._sequence,
        )
        self._sequence += 1
        return request

    def _drain_llm_queue(self) -> int:
        """Admit every LLM syscall currently waiting in the request queue.

        The queue getter blocks for a short timeout and then raises
        ``queue.Empty``, which doubles as the idle poll interval: this method
        returns as soon as the queue is momentarily empty.

        Returns:
            Number of requests admitted.
        """
        admitted = 0
        while self.active:
            try:
                syscall = self.get_llm_syscall()
            except Empty:
                return admitted
            except Exception:
                # A broken getter must not kill the scheduler thread and leave
                # every waiting agent blocked forever.
                logger.error("Failed to read from the LLM request queue:")
                traceback.print_exc()
                return admitted

            if syscall is None:
                continue

            with self._ready_lock:
                request = self._admit(syscall)
                self._ready.append(request)
                depth = len(self._ready)

            self._log_event(
                "QUEUED",
                f"{syscall.agent_name} ({self._label(request)})"
                f"  queue={depth}",
            )
            admitted += 1

        return admitted

    def _take_next(self) -> Optional[PendingRequest]:
        """Remove and return the most urgent ready request, if any."""
        with self._ready_lock:
            request = self.policy.select(self._ready, self._tick)
            if request is None:
                return None
            self._ready.remove(request)
            return request

    def _dispatch_llm_syscall(self, request: PendingRequest) -> None:
        """Execute one LLM syscall through the adapter.

        The adapter owns the rest of the syscall lifecycle (response, status,
        ``end_time`` and the event that unblocks the calling agent). On failure
        this method publishes an ``error`` status and sets the event, so a
        waiting agent is never left blocked.
        """
        syscall = request.payload
        details = self.policy.explain(request, self._tick)
        created_time = syscall.get_created_time()
        waited_seconds = (
            max(0.0, time.time() - created_time) if created_time else 0.0
        )
        try:
            syscall.set_status("executing")
            syscall.set_start_time(time.time())
            self._log_event(
                "RUN",
                f"{syscall.agent_name} ({self._label(request)})"
                f"  waited {waited_seconds:.1f}s / {details['wait_ticks']} rounds"
                f"  effective="
                f"{PriorityLevel(details['effective_level']).name.lower()}",
                "executing",
            )

            self.llm.execute_llm_syscalls([syscall])
            self._dispatched += 1

            start_time = syscall.get_start_time()
            took = max(0.0, time.time() - start_time) if start_time else 0.0
            self._log_event(
                "DONE",
                f"{syscall.agent_name}  took {took:.1f}s"
                f"  thread={syscall.get_pid()}",
                "done",
            )
            self._log_ready_set()
        except Exception as error:
            logger.error(
                "Error executing LLM syscall for %s: %s",
                getattr(syscall, "agent_name", "unknown"),
                error,
            )
            traceback.print_exc()
            self._log_event(
                "ERROR",
                f"{getattr(syscall, 'agent_name', 'unknown')} failed: {error}",
                "suspending",
            )
            try:
                syscall.set_status("error")
                syscall.set_end_time(time.time())
                syscall.event.set()
            except Exception:
                logger.error("Could not publish failure for %s", syscall)

    def process_llm_requests(self) -> None:
        """Admit arrivals, dispatch the best ready request, advance the tick.

        One dispatch round per iteration. The tick is the policy's notion of
        time: a request that is still in the ready set when the tick advances
        has aged by one round.
        """
        while self.active:
            self._drain_llm_queue()

            request = self._take_next()
            if request is None:
                # Nothing ready: reading the queue already blocked for the poll
                # interval, so just try again.
                continue

            self._dispatch_llm_syscall(request)

            with self._ready_lock:
                self._tick += 1

    def ready_snapshot(self) -> List[Dict[str, Any]]:
        """Describe the ready set in dispatch order (for metrics and demos)."""
        with self._ready_lock:
            return self.policy.snapshot(self._ready, self._tick)

    def drain_pending_syscalls(self) -> List[Any]:
        """Remove and return every accepted request still waiting to be dispatched.

        Unlike ``FIFOScheduler`` and ``RRScheduler``, this scheduler holds
        requests it has already taken off the request queue. Each of those is a
        thread blocked on ``syscall.join()`` waiting for a response, so if the
        scheduler is replaced at runtime (see ``aios.scheduler.manager``) they
        have to be handed back rather than dropped -- otherwise the agents
        behind them would block forever.

        Only safe once the processing threads have been stopped, because until
        then the ready set is still being mutated.
        """
        with self._ready_lock:
            pending = [request.payload for request in self._ready]
            self._ready.clear()
            return pending

    @property
    def dispatched_count(self) -> int:
        """Number of LLM syscalls this scheduler has dispatched."""
        return self._dispatched

    # ------------------------------------------------------------------
    # Non-LLM paths: arrival order, unchanged from FIFOScheduler
    # ------------------------------------------------------------------
    def _execute_syscall(
        self,
        syscall: Any,
        executor: Any,
        syscall_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Execute a memory/storage/tool syscall with status tracking.

        Args:
            syscall: The system call to execute.
            executor: Function that executes the syscall.
            syscall_type: Type name used for logging.

        Returns:
            The response, or ``None`` if execution failed.
        """
        try:
            syscall.set_status("executing")
            self.logger.log(
                f"{syscall.agent_name} is executing {syscall_type} syscall.\n",
                "executing",
            )
            syscall.set_start_time(time.time())

            response = executor(syscall)
            syscall.set_response(response)

            syscall.event.set()
            syscall.set_status("done")
            syscall.set_end_time(time.time())

            self.logger.log(
                f"Completed {syscall_type} syscall for {syscall.agent_name}. "
                f"Thread ID: {syscall.get_pid()}\n",
                "done",
            )
            return response

        except Exception as error:
            logger.error("Error executing %s syscall: %s", syscall_type, error)
            traceback.print_exc()
            return None

    def process_memory_requests(self) -> None:
        """Process Memory requests in arrival order."""
        while self.active:
            try:
                memory_syscall = self.get_memory_syscall()
            except Empty:
                continue
            self._execute_syscall(
                memory_syscall,
                self.memory_manager.address_request,
                "Memory",
            )

    def process_storage_requests(self) -> None:
        """Process Storage requests in arrival order."""
        while self.active:
            try:
                storage_syscall = self.get_storage_syscall()
            except Empty:
                continue
            self._execute_syscall(
                storage_syscall,
                self.storage_manager.address_request,
                "Storage",
            )

    def process_tool_requests(self) -> None:
        """Process Tool requests in arrival order."""
        while self.active:
            try:
                tool_syscall = self.get_tool_syscall()
            except Empty:
                continue
            self._execute_syscall(
                tool_syscall,
                self.tool_manager.address_request,
                "Tool",
            )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start all request processing threads."""
        self.active = True
        self.start_processing_threads(
            [
                self.process_llm_requests,
                self.process_memory_requests,
                self.process_storage_requests,
                self.process_tool_requests,
            ]
        )

    def stop(self) -> None:
        """Stop all processing threads gracefully."""
        self.active = False
        self.stop_processing_threads()
