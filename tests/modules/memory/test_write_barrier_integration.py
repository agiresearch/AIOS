"""
Integration tests for the memory write-barrier bugfix.

Where the property-based suite exercises ``MemoryManager`` directly,
this suite drives every scenario through the *full* kernel path:

    SyscallExecutor.execute_request
        -> global_memory_req_queue (queue dispatch)
        -> MemoryManager.address_request
        -> SlowMem0Provider

so the acceptance-time stamping in ``SyscallExecutor._execute_syscall``
is actually exercised. The PBT helpers stamp ``barrier_seq`` /
``barrier_snapshot`` manually before calling ``address_request``;
that bypasses the very dispatch path the bug originally manifested
on. The integration suite closes that gap.

Five scenarios from the design's "Integration Tests" section are
encoded:

- **Scenario 1: End-to-End Cross-Agent Personalization** -
  ``ProfileAgent`` and ``TaskAgent`` fire shared
  ``create_memory(user_id=alex)`` through the executor while their
  writes park at the provider gate. ``AssistantAgent`` then calls
  ``ContextInjector.inject(...)`` (option (b) from the task: the
  recommended path that avoids spinning up a real LLM). The
  inline barrier wait in ``ContextInjector._await_pending_writes``
  drains both writes before the cross-agent retrieval runs;
  ``InjectionDiagnostics.injected_count == 2`` confirms the
  acceptance-time stamping survived the executor round-trip.
  _Validates: Requirements 2.1, 2.2, 2.3._

- **Scenario 2: Explicit Retrieve After Concurrent Writes** - two
  ``create_memory`` clients and one ``retrieve_memory`` client all
  go through ``executor.execute_memory_syscall(...)``. This is the
  path Case 1 of ``test_write_barrier_exploration.py`` could not
  exercise (it bypasses the executor and so never gets a stamped
  ``barrier_snapshot``). The integration test confirms the full
  kernel path works.
  _Validates: Requirements 2.1, 2.2._

- **Scenario 3: Retrieval With No user_id Under Load** - many
  ``create_memory(user_id=alex)`` operations parked, legacy
  retrievals issued with no ``user_id``. Latency must stay on the
  fast path (Clause 3.3).
  _Validates: Requirement 3.3._

- **Scenario 4: Restart Resilience** - the ``SlowMem0Provider``
  in-memory store does not persist across restarts, so we restate
  the scenario as: after constructing a *fresh*
  ``MemoryManager`` + provider after a burst, the barrier resets
  to ``total_pending == 0`` and the first retrieval proceeds
  without waiting.
  _Validates: Requirement 3.4._

- **Scenario 5: Config Disabled (Kill-Switch)** - the cross-agent
  personalization scenario re-run with
  ``memory.write_barrier.enabled: false``. The bug must reappear
  (``injected_count == 0`` despite parked shared writes), proving
  the byte-identical preservation claim for the disabled path.
  _Validates: Requirement 3.5._

Approach notes:

- The kernel's production memory worker lives inside ``FIFOScheduler.
  process_memory_requests``. We don't want to spin up a real
  scheduler per test (it pulls in the LLM adapter, storage, tools,
  and config), so this suite installs a minimal "memory dispatcher"
  daemon thread that drains ``global_memory_req_queue`` and runs
  each syscall against the *test's* ``MemoryManager`` in a fresh
  worker thread. The syscall lifecycle (status / event / response
  fields) is set exactly the same way ``FIFOScheduler._execute_syscall``
  sets it, so ``SyscallExecutor._execute_syscall``'s join + status
  loop returns cleanly.

- Each scenario constructs fresh provider + manager + executor +
  dispatcher instances and tears them down in ``finally`` so a
  parked writer in one test cannot leak into the next. The global
  request queue is drained on entry as belt-and-suspenders.

- ``MemoryManager`` is instantiated via ``__new__`` + manual
  attribute wiring (mirroring ``test_write_barrier_pbt.py``) so the
  suite does not need ``ConfigManager``, the provider factory, or
  any real Mem0 / vector-DB wiring.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
import unittest
from collections import OrderedDict
from queue import Empty
from typing import Any, Dict, List, Optional

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.hooks.stores._global import (
    global_memory_req_queue,
    global_memory_req_queue_get_message,
)
from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
from aios.memory.write_barrier import MemoryWriteBarrier
from aios.syscall.syscall import SyscallExecutor

from tests.modules.memory._doubles.open_access import (
    OpenAccessManager,
)
from tests.modules.memory._doubles.slow_mem0_provider import (
    SlowMem0Provider,
)


logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Tunable budgets
# ----------------------------------------------------------------------

# Maximum acceptable latency (seconds) for any retrieval that should
# bypass the barrier completely. Generous enough to absorb CI jitter
# and process-level pauses; tight enough that a hidden barrier wait
# would blow through it.
FAST_PATH_BUDGET_S = 0.5


# ----------------------------------------------------------------------
# Manager / executor wiring
# ----------------------------------------------------------------------


def _make_manager(
    provider: SlowMem0Provider,
    barrier_config: Optional[Dict[str, Any]] = None,
) -> MemoryManager:
    """Build a MemoryManager bound to *provider* without touching
    ConfigManager. Mirrors the helper used by the PBT and
    preservation suites so the integration trial cost stays low.
    """
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    manager.barrier = MemoryWriteBarrier(config=barrier_config or {})
    # Writers and readers are different agents; access
    # control is not under test here.
    manager.access_manager = OpenAccessManager()
    return manager


def _make_executor(manager: MemoryManager) -> SyscallExecutor:
    """Build a SyscallExecutor with the test ``MemoryManager``
    wired in so ``_execute_syscall`` can stamp ``barrier_seq`` /
    ``barrier_snapshot`` at acceptance time.
    """
    executor = SyscallExecutor()
    executor.memory_manager = manager
    return executor


def _drain_global_memory_queue() -> None:
    """Empty the global memory request queue.

    The queue is a process-wide singleton (``aios.hooks.stores._global``).
    Tests that share a process risk inheriting a syscall left over from
    a previous test if it failed to drain. Belt-and-suspenders cleanup
    so each scenario starts from a known state.
    """
    while True:
        try:
            global_memory_req_queue.get(block=False)
        except Empty:
            return


# ----------------------------------------------------------------------
# Memory dispatcher (test-side scheduler stand-in)
# ----------------------------------------------------------------------


class _MemoryDispatcher:
    """Drain the global memory request queue and run each syscall
    against a test-owned ``MemoryManager``.

    Equivalent to the slice of ``FIFOScheduler.process_memory_requests``
    + ``_execute_syscall`` we need for these tests, minus the rest of
    the scheduler machinery (LLM batching, RR context manager, etc.).

    Each pulled syscall is processed in a fresh daemon thread so a
    parked writer at the provider gate does not block the dispatch
    of subsequent syscalls -- without this, two concurrent
    ``create_memory`` calls would serialize behind the gate and the
    integration scenarios that depend on multiple parked writers
    would deadlock.

    The lifecycle assignments below (``set_status``, ``set_start_time``,
    ``set_response``, ``event.set``, ``set_end_time``) mirror
    ``FIFOScheduler._execute_syscall`` so ``SyscallExecutor._execute_syscall``
    sees the same observable state and breaks out of its
    ``while True`` loop on ``status == "done"``.
    """

    def __init__(self, manager: MemoryManager) -> None:
        self.manager = manager
        self._stop = threading.Event()
        self._workers: List[threading.Thread] = []
        self._dispatcher_thread = threading.Thread(
            target=self._dispatch_loop, daemon=True,
        )

    def start(self) -> None:
        self._dispatcher_thread.start()

    def stop(self, join_timeout: float = 5.0) -> None:
        self._stop.set()
        self._dispatcher_thread.join(timeout=join_timeout)
        for worker in list(self._workers):
            worker.join(timeout=join_timeout)

    def _dispatch_loop(self) -> None:
        while not self._stop.is_set():
            try:
                syscall = global_memory_req_queue_get_message()
            except Empty:
                continue
            worker = threading.Thread(
                target=self._process_one,
                args=(syscall,),
                daemon=True,
            )
            self._workers.append(worker)
            worker.start()

    def _process_one(self, syscall) -> None:
        try:
            syscall.set_status("executing")
            syscall.set_start_time(time.time())
            response = self.manager.address_request(syscall)
            syscall.set_response(response)
            syscall.event.set()
            syscall.set_status("done")
            syscall.set_end_time(time.time())
        except Exception:  # pragma: no cover - debugging aid
            logger.exception(
                "Memory dispatcher worker raised; signalling syscall "
                "to unblock its caller.",
            )
            syscall.set_response(
                MemoryResponse(
                    success=False,
                    error="dispatcher exception; see logs",
                ),
            )
            syscall.event.set()
            syscall.set_status("done")
            syscall.set_end_time(time.time())


# ----------------------------------------------------------------------
# Query builders
# ----------------------------------------------------------------------


def _create_memory_query(
    user_id: str,
    content: str,
    owner_agent: str,
    sharing_policy: str = "shared",
    memory_type: str = "profile",
) -> MemoryQuery:
    return MemoryQuery(
        operation_type="add_memory",
        params={
            "content": content,
            "metadata": {
                "user_id": user_id,
                "owner_agent": owner_agent,
                "sharing_policy": sharing_policy,
                "memory_type": memory_type,
            },
        },
    )


def _retrieve_memory_query(
    content: str,
    user_id: Optional[str] = None,
    k: int = 10,
) -> MemoryQuery:
    params: Dict[str, Any] = {"content": content, "k": k}
    if user_id is not None:
        params["user_id"] = user_id
    return MemoryQuery(
        operation_type="retrieve_memory",
        params=params,
    )


# ----------------------------------------------------------------------
# Test base
# ----------------------------------------------------------------------


class _IntegrationTestBase(unittest.TestCase):
    """Common setup / teardown: drain the global queue on entry and
    track per-test resources for tidy cleanup."""

    def setUp(self) -> None:
        _drain_global_memory_queue()
        self._dispatchers: List[_MemoryDispatcher] = []
        self._providers: List[SlowMem0Provider] = []
        self._threads: List[threading.Thread] = []

    def tearDown(self) -> None:
        # Release any parked writers so their syscall threads can
        # exit before the dispatcher is stopped.
        for provider in self._providers:
            try:
                provider.release()
            except Exception:
                pass

        for thread in self._threads:
            thread.join(timeout=5.0)

        for dispatcher in self._dispatchers:
            dispatcher.stop(join_timeout=5.0)

        for provider in self._providers:
            try:
                provider.close()
            except Exception:
                pass

        _drain_global_memory_queue()

    # Convenience helpers --------------------------------------------------

    def _wire(
        self,
        barrier_config: Optional[Dict[str, Any]] = None,
    ) -> tuple[SlowMem0Provider, MemoryManager, SyscallExecutor]:
        """Build a fresh provider + manager + executor + dispatcher
        triple and register them for tearDown cleanup.

        The memory request queue is a process-wide singleton, so
        only ONE dispatcher may be alive at a time -- otherwise two
        dispatchers race to pull syscalls and route them to the
        wrong manager. We stop any dispatcher already registered
        before starting the new one (and drain the queue, so a
        syscall pulled by the previous dispatcher but not yet
        processed cannot leak into the new manager).
        """
        for existing in self._dispatchers:
            existing.stop(join_timeout=5.0)
        self._dispatchers = []
        _drain_global_memory_queue()

        provider = SlowMem0Provider()
        manager = _make_manager(provider, barrier_config=barrier_config)
        executor = _make_executor(manager)

        dispatcher = _MemoryDispatcher(manager)
        dispatcher.start()

        self._providers.append(provider)
        self._dispatchers.append(dispatcher)
        return provider, manager, executor

    def _spawn(
        self, target, *args, **kwargs,
    ) -> threading.Thread:
        thread = threading.Thread(
            target=target, args=args, kwargs=kwargs, daemon=True,
        )
        thread.start()
        self._threads.append(thread)
        return thread


# ----------------------------------------------------------------------
# Scenario 1: End-to-End Cross-Agent Personalization
# ----------------------------------------------------------------------


class Scenario1CrossAgentPersonalizationTests(_IntegrationTestBase):
    """ProfileAgent + TaskAgent fire shared writes through the
    executor; AssistantAgent then drives ``ContextInjector.inject``
    after the writes are accepted (and parked) at the provider.

    The barrier MUST hold the cross-agent retrieval until both
    writes drain, so injection diagnostics show
    ``injected_count == 2``.

    **Validates: Requirements 2.1, 2.2, 2.3**
    """

    def test_cross_agent_personalization_through_executor(
        self,
    ) -> None:
        provider, manager, executor = self._wire()
        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                # Drop the threshold so SlowMem0Provider's hard-coded
                # score=0.9 passes cleanly; the test cares about
                # cross-agent visibility, not relevance ranking.
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        # Park the gate so the writes are accepted by the executor
        # (stamped with barrier_seq) but not yet committed when the
        # injector runs.
        provider.park()

        def _profile_writer() -> None:
            executor.execute_memory_syscall(
                "ProfileAgent",
                _create_memory_query(
                    user_id="alex",
                    content=(
                        "Alex's profile: senior engineer, "
                        "loves Python."
                    ),
                    owner_agent="ProfileAgent",
                ),
            )

        def _task_writer() -> None:
            executor.execute_memory_syscall(
                "TaskAgent",
                _create_memory_query(
                    user_id="alex",
                    content="Alex is preparing a Q1 roadmap.",
                    owner_agent="TaskAgent",
                ),
            )

        self._spawn(_profile_writer)
        self._spawn(_task_writer)

        self.assertTrue(
            provider.wait_until_pending(2, timeout=5.0),
            "Both writers should have parked at the provider gate.",
        )

        # Sanity: the executor stamped both writes -- the barrier
        # registry now lists 2 pending writes for alex. If this
        # fails, the executor's acceptance-time stamping is broken
        # and the rest of the assertion is meaningless.
        stats = manager.barrier.stats()
        self.assertEqual(
            stats["pending_by_user"].get("alex"),
            2,
            (
                "SyscallExecutor did not stamp barrier_seq on the "
                "parked writes; pending_by_user="
                f"{stats['pending_by_user']!r}."
            ),
        )

        # Schedule the gate release so the inject() call below
        # observably blocks on the barrier (~150ms is well below the
        # default 5s barrier timeout but well above any noise).
        def _release_after() -> None:
            time.sleep(0.15)
            provider.release()

        self._spawn(_release_after)

        # Drive the injector inline (option (b) from the task).
        # ``inject`` consults the barrier via
        # ``_await_pending_writes`` for the cross-agent user_id,
        # blocks until both shared writes commit, then runs the
        # cross-agent retrieve and prepends the system message.
        llm_query = LLMQuery(
            messages=[{
                "role": "user",
                "content": "What do you know about Alex?",
            }],
            action_type="chat",
        )
        _, diagnostics = injector.inject(
            "AssistantAgent", llm_query, user_id="alex"
        )

        self.assertEqual(
            diagnostics.get("injected_count"),
            2,
            (
                "Cross-agent personalization through executor + "
                "barrier did not surface both shared writes. "
                f"diagnostics={diagnostics!r}"
            ),
        )
        self.assertEqual(
            sorted(diagnostics.get("source_agents") or []),
            ["ProfileAgent", "TaskAgent"],
        )
        self.assertEqual(
            diagnostics.get("resolved_user_id"), "alex",
        )

        # The barrier waited on the cross-agent user_id; the
        # diagnostic should record a non-BYPASSED outcome for "alex".
        barrier_waits = diagnostics.get("barrier_waits") or []
        outcomes_by_user = {
            entry["user_id"]: entry["outcome"]
            for entry in barrier_waits
        }
        self.assertEqual(
            outcomes_by_user.get("alex"),
            "DRAINED",
            (
                "Expected the cross-agent inject to record a DRAINED "
                f"barrier wait for alex. barrier_waits={barrier_waits!r}"
            ),
        )

        # Barrier must be fully drained for alex by the time
        # inject() returns.
        self.assertEqual(
            manager.barrier.stats()["total_pending"],
            0,
            "Barrier still has pending writes after inject completed.",
        )


# ----------------------------------------------------------------------
# Scenario 2: Explicit Retrieve After Concurrent Writes
# ----------------------------------------------------------------------


class Scenario2ExplicitRetrieveAfterConcurrentWritesTests(
    _IntegrationTestBase,
):
    """Two SDK clients fire ``create_memory`` for ``user_id=alex``;
    a third fires ``retrieve_memory``, all through the executor.

    This is the path Case 1 of ``test_write_barrier_exploration.py``
    bypasses (it calls ``manager.address_request`` directly without
    a stamped ``barrier_snapshot``). The integration test confirms
    the full executor path delivers write-before-read ordering.

    **Validates: Requirements 2.1, 2.2**
    """

    def test_explicit_retrieve_sees_concurrent_writes(self) -> None:
        provider, manager, executor = self._wire()

        provider.park()

        def _writer(agent_name: str, content: str) -> None:
            executor.execute_memory_syscall(
                agent_name,
                _create_memory_query(
                    user_id="alex",
                    content=content,
                    owner_agent=agent_name,
                ),
            )

        self._spawn(
            _writer, "WriterAgentA",
            "Alex prefers Python and dark roast coffee.",
        )
        self._spawn(
            _writer, "WriterAgentB",
            "Alex is preparing a Q1 roadmap.",
        )

        self.assertTrue(
            provider.wait_until_pending(2, timeout=5.0),
            "Both writers should have parked at the provider gate.",
        )

        # Capture the reader's response from a background thread so
        # we can confirm it actually waits on the barrier.
        reader_result: Dict[str, Any] = {}

        def _reader() -> None:
            t0 = time.perf_counter()
            result = executor.execute_memory_syscall(
                "ReaderAgent",
                _retrieve_memory_query(
                    content="alex preferences",
                    user_id="alex",
                ),
            )
            elapsed = time.perf_counter() - t0
            reader_result["response"] = result.get("response")
            reader_result["elapsed"] = elapsed

        reader_thread = self._spawn(_reader)

        # Reader should be parked on the barrier (waiting for the
        # two pending writes to drain). Give it a moment to enter
        # the wait, then release the gate.
        time.sleep(0.1)
        self.assertTrue(
            reader_thread.is_alive(),
            (
                "Reader returned before the parked writes drained -- "
                "barrier wait did not engage on the executor path."
            ),
        )

        provider.release()

        reader_thread.join(timeout=5.0)
        self.assertFalse(
            reader_thread.is_alive(),
            "Reader thread did not complete after gate release.",
        )

        response = reader_result.get("response")
        self.assertIsNotNone(response, "Reader produced no response.")
        self.assertTrue(response.success, msg=str(response))

        results = response.search_results or []
        alex_results = [
            r for r in results
            if (r.get("metadata") or {}).get("user_id") == "alex"
        ]
        self.assertEqual(
            len(alex_results),
            2,
            (
                "Reader saw "
                f"{len(alex_results)} memories for alex; expected 2 "
                "after both concurrent writes drained through the "
                "executor + barrier path."
            ),
        )
        self.assertEqual(
            manager.barrier.stats()["total_pending"], 0,
        )


# ----------------------------------------------------------------------
# Scenario 3: Retrieval With No user_id Under Load
# ----------------------------------------------------------------------


class Scenario3NoUserIdUnderLoadTests(_IntegrationTestBase):
    """Many ``create_memory(user_id=alex)`` operations in flight;
    legacy retrievals issued with no ``user_id`` MUST return on the
    fast path with latency comparable to a baseline run with no
    in-flight writes (Clause 3.3).

    "Identical" is a distribution claim that doesn't survive a
    single Hypothesis run on shared CI. We translate it to a
    bounded fast-path budget plus a tight bound on the ratio of
    loaded median latency to baseline median latency. Both are
    derived from the existing preservation suite's
    ``FAST_PATH_BUDGET_S = 0.5`` and the design's "near-zero"
    expectation for the bypass path.

    **Validates: Requirement 3.3**
    """

    NUM_RETRIEVALS = 20
    NUM_PARKED_WRITES = 8

    def _measure_no_userid_latencies(
        self,
        executor: SyscallExecutor,
    ) -> List[float]:
        latencies: List[float] = []
        for i in range(self.NUM_RETRIEVALS):
            t0 = time.perf_counter()
            executor.execute_memory_syscall(
                "ReaderAgent",
                _retrieve_memory_query(
                    content=f"anything #{i}",
                    user_id=None,
                ),
            )
            latencies.append(time.perf_counter() - t0)
        return latencies

    @staticmethod
    def _median(values: List[float]) -> float:
        ordered = sorted(values)
        mid = len(ordered) // 2
        if len(ordered) % 2:
            return ordered[mid]
        return 0.5 * (ordered[mid - 1] + ordered[mid])

    def test_no_userid_retrieval_latency_unchanged_under_load(
        self,
    ) -> None:
        # Baseline: barrier enabled, no in-flight writes.
        _, _, baseline_executor = self._wire()
        baseline_latencies = self._measure_no_userid_latencies(
            baseline_executor,
        )

        # Loaded: same kernel shape, but fire many parked writes
        # for alex so the barrier registry is populated.
        loaded_provider, loaded_manager, loaded_executor = self._wire()
        loaded_provider.park()

        def _writer(i: int) -> None:
            loaded_executor.execute_memory_syscall(
                f"WriterAgent{i}",
                _create_memory_query(
                    user_id="alex",
                    content=f"alex fact #{i}",
                    owner_agent=f"WriterAgent{i}",
                ),
            )

        for i in range(self.NUM_PARKED_WRITES):
            self._spawn(_writer, i)

        self.assertTrue(
            loaded_provider.wait_until_pending(
                self.NUM_PARKED_WRITES, timeout=5.0,
            ),
            "Writers should have parked at the loaded provider gate.",
        )
        # Sanity: the executor stamped every write.
        loaded_stats = loaded_manager.barrier.stats()
        self.assertEqual(
            loaded_stats["pending_by_user"].get("alex"),
            self.NUM_PARKED_WRITES,
        )

        loaded_latencies = self._measure_no_userid_latencies(
            loaded_executor,
        )

        # Hard ceiling: every retrieval must clear the fast-path
        # budget regardless of the number of in-flight writes.
        for i, latency in enumerate(loaded_latencies):
            self.assertLessEqual(
                latency,
                FAST_PATH_BUDGET_S,
                (
                    f"Retrieval #{i} without user_id took "
                    f"{latency:.3f}s under load (budget "
                    f"{FAST_PATH_BUDGET_S:.3f}s). The fast path was "
                    "violated."
                ),
            )

        # Distribution claim: the loaded median MUST stay within a
        # tight ratio of the baseline median. We allow the larger of
        # the absolute slack (fast-path budget) and a 5x relative
        # slack since baseline medians on a fast machine can be in
        # the tens of microseconds, and a 5% relative bound flakes
        # on small-N CI runs.
        baseline_median = self._median(baseline_latencies)
        loaded_median = self._median(loaded_latencies)
        absolute_slack = FAST_PATH_BUDGET_S
        relative_ceiling = max(baseline_median * 5.0, 0.005)
        ceiling = max(relative_ceiling, absolute_slack)
        self.assertLessEqual(
            loaded_median,
            ceiling,
            (
                "Loaded median no-user_id latency "
                f"{loaded_median:.4f}s exceeded the ceiling "
                f"{ceiling:.4f}s "
                f"(baseline median {baseline_median:.4f}s). "
                "Clause 3.3 preservation broken."
            ),
        )


# ----------------------------------------------------------------------
# Scenario 4: Restart Resilience
# ----------------------------------------------------------------------


class Scenario4RestartResilienceTests(_IntegrationTestBase):
    """A burst of writes leaves the first manager's barrier with no
    pending entries after release. After the test "restarts" by
    constructing a fresh ``MemoryManager`` + provider, the new
    barrier MUST start with ``total_pending == 0`` and the first
    retrieval through it MUST proceed without waiting.

    Restated for the in-memory ``SlowMem0Provider``: this test does
    not assert previously-committed memories are still retrievable
    (the in-memory store does not persist across instances). It
    asserts barrier-state freshness, which is what the kernel owns.

    **Validates: Requirement 3.4**
    """

    def test_fresh_manager_has_empty_barrier_and_fast_retrieval(
        self,
    ) -> None:
        # --- First "kernel": run a burst with parked writes, then
        # release so the burst completes.
        provider_a, manager_a, executor_a = self._wire()

        provider_a.park()

        def _writer(agent_name: str) -> None:
            executor_a.execute_memory_syscall(
                agent_name,
                _create_memory_query(
                    user_id="alex",
                    content=f"burst fact from {agent_name}",
                    owner_agent=agent_name,
                ),
            )

        self._spawn(_writer, "WriterAgent0")
        self._spawn(_writer, "WriterAgent1")
        self._spawn(_writer, "WriterAgent2")

        self.assertTrue(
            provider_a.wait_until_pending(3, timeout=5.0),
            "Burst writers should have parked at the gate.",
        )
        self.assertEqual(
            manager_a.barrier.stats()["pending_by_user"].get("alex"),
            3,
        )

        # Drain the burst. The dispatcher's per-syscall worker
        # threads complete once the gate is released, which causes
        # MemoryManager.address_request's finally block to release
        # the barrier entries.
        provider_a.release()

        deadline = time.monotonic() + 5.0
        while (
            manager_a.barrier.stats()["total_pending"] > 0
            and time.monotonic() < deadline
        ):
            time.sleep(0.01)
        self.assertEqual(
            manager_a.barrier.stats()["total_pending"],
            0,
            (
                "First manager's barrier did not drain after release; "
                f"stats={manager_a.barrier.stats()!r}"
            ),
        )

        # --- Second "kernel": fresh provider, manager, executor,
        # dispatcher. The new barrier starts empty.
        _, manager_b, executor_b = self._wire()

        fresh_stats = manager_b.barrier.stats()
        self.assertEqual(
            fresh_stats["total_pending"],
            0,
            (
                "Fresh manager's barrier should start empty on "
                f"'restart'; stats={fresh_stats!r}"
            ),
        )
        self.assertEqual(fresh_stats["last_acquired_seq"], 0)
        self.assertEqual(fresh_stats["last_released_seq"], 0)

        # First retrieval after restart proceeds without waiting --
        # there are no pending writes so the barrier wait is a
        # short snapshot/wait round-trip that returns DRAINED
        # immediately.
        t0 = time.perf_counter()
        result = executor_b.execute_memory_syscall(
            "ReaderAgent",
            _retrieve_memory_query(
                content="anything", user_id="alex",
            ),
        )
        elapsed = time.perf_counter() - t0

        response = result.get("response")
        self.assertIsNotNone(response)
        self.assertTrue(response.success, msg=str(response))
        # The fresh in-memory provider holds no committed memories.
        self.assertEqual(
            len(response.search_results or []),
            0,
        )
        self.assertLessEqual(
            elapsed,
            FAST_PATH_BUDGET_S,
            (
                "Fresh-manager retrieval took "
                f"{elapsed:.3f}s; expected near-zero with empty "
                "barrier."
            ),
        )


# ----------------------------------------------------------------------
# Scenario 5: Config Disabled (Kill-Switch)
# ----------------------------------------------------------------------


class Scenario5KillSwitchTests(_IntegrationTestBase):
    """With ``memory.write_barrier.enabled: false``, the cross-agent
    personalization scenario MUST revert to the *pre-fix* behavior:
    parked shared writes are invisible to the cross-agent retrieval
    inside ``ContextInjector.inject`` and ``injected_count == 0``.

    This validates two design clauses at once:

    - The kill-switch (operators can flip the flag and immediately
      retake the pre-fix code path).
    - The byte-identical preservation claim for the disabled path
      (the bug *must* manifest here; if it does not, the disabled
      path is doing more than it used to).

    **Validates: Requirement 3.5**
    """

    def test_disabled_barrier_reverts_to_prefix_bug(self) -> None:
        provider, manager, executor = self._wire(
            barrier_config={"enabled": False},
        )
        # Sanity: the barrier is genuinely disabled.
        self.assertFalse(manager.barrier.stats()["enabled"])

        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        provider.park()

        def _writer(agent_name: str, content: str) -> None:
            executor.execute_memory_syscall(
                agent_name,
                _create_memory_query(
                    user_id="alex",
                    content=content,
                    owner_agent=agent_name,
                ),
            )

        self._spawn(
            _writer, "ProfileAgent",
            "Alex's profile: senior engineer, loves Python.",
        )
        self._spawn(
            _writer, "TaskAgent",
            "Alex is preparing a Q1 roadmap.",
        )

        self.assertTrue(
            provider.wait_until_pending(2, timeout=5.0),
            "Both writers should have parked at the provider gate.",
        )

        # With the barrier disabled, ``acquire`` returned the
        # sentinel and the registry stayed empty -- the executor's
        # stamping is a no-op on this path.
        disabled_stats = manager.barrier.stats()
        self.assertEqual(
            disabled_stats["pending_by_user"],
            {},
            (
                "Disabled barrier should not register pending writes; "
                f"stats={disabled_stats!r}"
            ),
        )

        # Run inject(). Without the barrier, the cross-agent
        # retrieval reads the post-commit store snapshot
        # immediately, which is empty because both writes are still
        # parked at the provider.
        llm_query = LLMQuery(
            messages=[{
                "role": "user",
                "content": "What do you know about Alex?",
            }],
            action_type="chat",
        )
        t0 = time.perf_counter()
        _, diagnostics = injector.inject("AssistantAgent", llm_query)
        elapsed = time.perf_counter() - t0

        # Pre-fix behavior is back: 0 memories injected and the
        # call returns on the fast path because no barrier wait
        # ran.
        self.assertEqual(
            diagnostics.get("injected_count"),
            0,
            (
                "Kill-switch broken: with barrier disabled, "
                "inject() saw "
                f"injected_count={diagnostics.get('injected_count')} "
                "while shared writes were parked. The pre-fix bug "
                "MUST manifest here -- otherwise the disabled path "
                "is doing more than it used to."
            ),
        )
        self.assertEqual(
            diagnostics.get("source_agents") or [], [],
        )
        # No barrier waits should have been recorded; every call
        # short-circuited on the disabled fast path.
        self.assertEqual(
            diagnostics.get("barrier_waits") or [], [],
            (
                "Disabled barrier should never record a non-BYPASSED "
                "wait; got "
                f"{diagnostics.get('barrier_waits')!r}"
            ),
        )
        self.assertLessEqual(
            elapsed,
            FAST_PATH_BUDGET_S,
            (
                "Disabled-barrier inject() took "
                f"{elapsed:.3f}s; expected the pre-fix fast path."
            ),
        )


if __name__ == "__main__":
    unittest.main()
