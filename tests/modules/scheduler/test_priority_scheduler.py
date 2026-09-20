"""Integration tests for PriorityScheduler against the real AIOS interfaces.

``priority_scheduler`` subclasses ``aios.scheduler.base.BaseScheduler``, which
pulls in the whole AIOS component stack, so importing ``cerebrum`` is a
prerequisite and these tests are skipped when it is missing. The scheduling
*decisions* themselves are covered without any AIOS dependency in
``test_priority_policy.py``.

The fake LLM adapter records dispatch order and reproduces the parts of the
syscall lifecycle the real adapter owns (status, response, ``end_time`` and the
event that unblocks the calling agent).
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from queue import Queue
from typing import Any, List, Optional

import pytest

from aios.scheduler.priority_policy import PriorityLevel

pytest.importorskip("cerebrum")

from aios.scheduler.fifo_scheduler import FIFOScheduler  # noqa: E402
from aios.scheduler.priority_scheduler import (  # noqa: E402
    POLICY_NAME,
    PriorityScheduler,
)
from aios.scheduler.registry import (  # noqa: E402
    POLICY_FIFO,
    POLICY_PRIORITY,
    POLICY_ROUND_ROBIN,
    build_scheduler_params,
    create_scheduler,
)
from aios.scheduler.rr_scheduler import RRScheduler  # noqa: E402


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------
class FakeSyscall:
    """Minimal stand-in for ``aios.syscall.Syscall``."""

    def __init__(self, agent_name: str, priority: Any = None):
        self.agent_name = agent_name
        self.priority = priority
        self.status: Optional[str] = None
        self.created_time: Optional[float] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.response: Any = None
        self.event = threading.Event()

    def get_priority(self):
        return self.priority

    def get_created_time(self):
        # Real ``Syscall`` timestamps are set by ``SyscallExecutor`` before
        # the request is queued; mirror the accessor so the scheduler's
        # wait-time logging takes the same path here as in the kernel.
        return self.created_time

    def get_start_time(self):
        return self.start_time

    def set_priority(self, value):
        self.priority = value

    def set_status(self, value):
        self.status = value

    def get_status(self):
        return self.status

    def set_start_time(self, value):
        self.start_time = value

    def set_end_time(self, value):
        self.end_time = value

    def set_response(self, value):
        self.response = value

    def get_pid(self):
        return id(self)


class RecordingLLM:
    """Stand-in for ``LLMAdapter`` that records dispatch order."""

    def __init__(self, gate: Optional[threading.Event] = None):
        self.dispatched: List[str] = []
        self.started = threading.Event()
        self._gate = gate

    def execute_llm_syscalls(self, llm_syscalls):
        self.started.set()
        if self._gate is not None:
            # Hold the dispatch open so the ready set can be inspected.
            self._gate.wait(timeout=5)
        for syscall in llm_syscalls:
            self.dispatched.append(syscall.agent_name)
            syscall.set_status("done")
            syscall.set_response("ok")
            syscall.set_end_time(time.time())
            syscall.event.set()


class FailingLLM:
    """Adapter whose backend is unavailable."""

    def execute_llm_syscalls(self, llm_syscalls):
        raise RuntimeError("backend unavailable")


class FakeManager:
    """Stand-in for a memory/storage/tool manager."""

    def address_request(self, syscall):
        return {"handled": syscall.agent_name}


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def make_queue_getter(queue: Queue, timeout: float = 0.05):
    """Mimic ``aios/hooks/stores/queue.py``: a bounded blocking get."""

    def getter():
        return queue.get(block=True, timeout=timeout)

    return getter


def make_scheduler(llm: Any, queue: Queue, **kwargs) -> PriorityScheduler:
    return PriorityScheduler(
        llm=llm,
        memory_manager=None,
        storage_manager=None,
        tool_manager=None,
        log_mode="console",
        get_llm_syscall=make_queue_getter(queue),
        get_memory_syscall=None,
        get_storage_syscall=None,
        get_tool_syscall=None,
        **kwargs,
    )


@contextmanager
def llm_dispatch_thread(scheduler: PriorityScheduler):
    """Run only the LLM processor in a thread, as ``start`` would."""
    scheduler.active = True
    thread = threading.Thread(target=scheduler.process_llm_requests, daemon=True)
    thread.start()
    try:
        yield thread
    finally:
        scheduler.active = False
        thread.join(timeout=5)


def wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def run_until_dispatched(scheduler, llm, expected: int, timeout: float = 5.0) -> bool:
    with llm_dispatch_thread(scheduler):
        return wait_until(lambda: len(llm.dispatched) >= expected, timeout)


# ----------------------------------------------------------------------
# Dispatch order
# ----------------------------------------------------------------------
def test_higher_priority_syscall_is_dispatched_first():
    """A HIGH request queued *after* a LOW one is still served first."""
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=10)
    queue.put(FakeSyscall("low_agent", PriorityLevel.LOW))
    queue.put(FakeSyscall("high_agent", PriorityLevel.HIGH))

    assert run_until_dispatched(scheduler, llm, 2)
    assert llm.dispatched[:2] == ["high_agent", "low_agent"]


def test_equal_priority_keeps_arrival_order():
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=10)
    for name in ("first", "second", "third"):
        queue.put(FakeSyscall(name, PriorityLevel.NORMAL))

    assert run_until_dispatched(scheduler, llm, 3)
    assert llm.dispatched[:3] == ["first", "second", "third"]


def test_aging_eventually_dispatches_a_low_priority_syscall():
    """With aging_interval=1 the LOW request reaches level 0 after two rounds."""
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=1)
    queue.put(FakeSyscall("low_agent", PriorityLevel.LOW))
    queue.put(FakeSyscall("high_agent_1", PriorityLevel.HIGH))
    queue.put(FakeSyscall("high_agent_2", PriorityLevel.HIGH))

    assert run_until_dispatched(scheduler, llm, 3)
    assert llm.dispatched[:3] == ["high_agent_1", "high_agent_2", "low_agent"]


def test_string_priorities_are_accepted_from_the_syscall():
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=10)
    queue.put(FakeSyscall("low_agent", "low"))
    queue.put(FakeSyscall("high_agent", "urgent"))

    assert run_until_dispatched(scheduler, llm, 2)
    assert llm.dispatched[:2] == ["high_agent", "low_agent"]


def test_unset_priority_falls_back_to_the_configured_default():
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(
        llm,
        queue,
        aging_interval=10,
        default_priority=PriorityLevel.HIGH,
    )
    queue.put(FakeSyscall("unset_agent", None))
    queue.put(FakeSyscall("low_agent", PriorityLevel.LOW))

    assert run_until_dispatched(scheduler, llm, 2)
    assert llm.dispatched[:2] == ["unset_agent", "low_agent"]


def test_a_real_aios_syscall_can_be_priority_scheduled():
    """The policy works on genuine ``LLMSyscall`` objects, not just fakes."""
    import aios.syscall.syscall  # noqa: F401  (resolves a pre-existing cycle)
    from aios.syscall.llm import LLMSyscall
    from cerebrum.llm.apis import LLMQuery

    def make(agent_name, priority):
        syscall = LLMSyscall(
            agent_name,
            LLMQuery(
                messages=[{"role": "user", "content": "hello"}],
                action_type="chat",
            ),
        )
        syscall.set_priority(priority)
        return syscall

    scheduler = make_scheduler(RecordingLLM(), Queue())
    low = scheduler._admit(make("low_agent", PriorityLevel.LOW))
    high = scheduler._admit(make("high_agent", PriorityLevel.HIGH))

    chosen = scheduler.policy.select([low, high], now_tick=0)

    assert chosen is high
    assert chosen.payload.get_priority() == PriorityLevel.HIGH
    assert low.payload.get_priority() == PriorityLevel.LOW


# ----------------------------------------------------------------------
# Dispatch lifecycle
# ----------------------------------------------------------------------
def test_dispatched_syscall_is_marked_done_and_unblocked():
    llm = RecordingLLM()
    scheduler = make_scheduler(llm, Queue())
    syscall = FakeSyscall("agent", PriorityLevel.NORMAL)

    scheduler._dispatch_llm_syscall(scheduler._admit(syscall))

    assert syscall.status == "done"
    assert syscall.response == "ok"
    assert syscall.start_time is not None and syscall.end_time is not None
    assert syscall.event.is_set()
    assert scheduler.dispatched_count == 1


def test_failed_dispatch_does_not_leave_the_agent_blocked():
    scheduler = make_scheduler(FailingLLM(), Queue())
    syscall = FakeSyscall("agent", PriorityLevel.NORMAL)

    scheduler._dispatch_llm_syscall(scheduler._admit(syscall))

    assert syscall.status == "error"
    assert syscall.end_time is not None
    assert syscall.event.is_set()
    assert scheduler.dispatched_count == 0


def test_non_llm_syscall_reports_success_and_unblocks():
    """Memory/storage/tool requests keep the FIFO behaviour."""
    scheduler = make_scheduler(RecordingLLM(), Queue())
    syscall = FakeSyscall("memory_agent", PriorityLevel.NORMAL)

    response = scheduler._execute_syscall(
        syscall, FakeManager().address_request, "Memory"
    )

    assert response == {"handled": "memory_agent"}
    assert syscall.status == "done"
    assert syscall.response == {"handled": "memory_agent"}
    assert syscall.event.is_set()


# ----------------------------------------------------------------------
# Observability
# ----------------------------------------------------------------------
def test_ready_snapshot_exposes_the_pending_decision():
    gate = threading.Event()
    llm = RecordingLLM(gate=gate)
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=5)
    queue.put(FakeSyscall("high_agent", PriorityLevel.HIGH))
    queue.put(FakeSyscall("low_agent", PriorityLevel.LOW))

    with llm_dispatch_thread(scheduler):
        assert wait_until(lambda: llm.started.is_set())
        assert wait_until(lambda: len(scheduler.ready_snapshot()) == 1)

        snapshot = scheduler.ready_snapshot()
        assert snapshot[0]["payload"].agent_name == "low_agent"
        assert snapshot[0]["base_priority"] is PriorityLevel.LOW
        assert snapshot[0]["effective_level"] == int(PriorityLevel.LOW)

        gate.set()
        assert wait_until(lambda: len(llm.dispatched) == 2)

    assert llm.dispatched[:2] == ["high_agent", "low_agent"]


# ----------------------------------------------------------------------
# Registry contract: selecting a policy by name from config.yaml
# ----------------------------------------------------------------------
def base_params(llm: Any) -> dict:
    return dict(
        llm=llm,
        memory_manager=None,
        storage_manager=None,
        tool_manager=None,
        log_mode="console",
        get_llm_syscall=None,
        get_memory_syscall=None,
        get_storage_syscall=None,
        get_tool_syscall=None,
    )


def test_policy_name_is_the_registry_key():
    assert POLICY_NAME == POLICY_PRIORITY


def test_create_scheduler_builds_every_configured_policy():
    params = base_params(RecordingLLM())

    priority = create_scheduler("priority", **params, aging_interval=7)
    assert isinstance(priority, PriorityScheduler)
    assert priority.policy.aging_interval == 7
    assert priority.active is False

    assert isinstance(create_scheduler("fifo", **params), FIFOScheduler)
    assert isinstance(create_scheduler("fcfs", **params), FIFOScheduler)
    assert isinstance(
        create_scheduler("round_robin", **params, time_slice=0.5), RRScheduler
    )


def test_build_scheduler_params_reads_the_policy_and_its_options():
    components = {
        "llms": RecordingLLM(),
        "memory": None,
        "storage": None,
        "tool": None,
    }
    config = {
        "log_mode": "console",
        "policy": "priority",
        "priority": {"aging_interval": 3, "default_priority": "high"},
    }

    policy, params = build_scheduler_params(components, config)
    scheduler = create_scheduler(policy, **params)

    assert policy == POLICY_PRIORITY
    assert params["llm"] is components["llms"]
    assert params["aging_interval"] == 3
    assert scheduler.policy.aging_interval == 3
    assert scheduler.policy.default_priority is PriorityLevel.HIGH


@pytest.mark.parametrize(
    "config,use_context,expected",
    [
        ({}, False, POLICY_FIFO),
        ({}, True, POLICY_ROUND_ROBIN),
        ({"policy": "priority"}, False, POLICY_PRIORITY),
        ({"policy": "priority"}, True, POLICY_PRIORITY),
    ],
)
def test_build_scheduler_params_resolves_the_policy(config, use_context, expected):
    components = {
        "llms": RecordingLLM(),
        "memory": None,
        "storage": None,
        "tool": None,
    }

    policy, params = build_scheduler_params(
        components, config, use_context_manager=use_context
    )

    assert policy == expected
    # Queue getters are filled in from the kernel's global request queues, so a
    # scheduler built from config.yaml reads the same queues as one built
    # through the hook functions.
    for name in (
        "get_llm_syscall",
        "get_memory_syscall",
        "get_storage_syscall",
        "get_tool_syscall",
    ):
        assert callable(params[name])


# ----------------------------------------------------------------------
# Live allocation log
# ----------------------------------------------------------------------
class RecordingLogger:
    """Captures scheduler log lines instead of printing them."""

    def __init__(self) -> None:
        self.lines: List[Any] = []

    def log(self, content: str, level: str) -> None:
        self.lines.append((level, content.strip()))

    def tags(self) -> List[str]:
        return [text.split()[0] for _, text in self.lines]

    def text_for(self, tag: str) -> Optional[str]:
        for _, text in self.lines:
            if text.startswith(tag):
                return text
        return None


def test_live_log_reports_queue_run_and_done():
    """A dispatch emits QUEUED, RUN and DONE lines for the kernel terminal."""
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=10)
    scheduler.logger = RecordingLogger()

    queue.put(FakeSyscall("high_agent", PriorityLevel.HIGH))

    assert run_until_dispatched(scheduler, llm, 1)

    tags = scheduler.logger.tags()
    assert "QUEUED" in tags
    assert "RUN" in tags
    assert "DONE" in tags

    queued = scheduler.logger.text_for("QUEUED")
    assert "high_agent" in queued
    assert "high" in queued

    run = scheduler.logger.text_for("RUN")
    assert "high_agent" in run
    assert "waited" in run
    assert "effective=high" in run


def test_live_log_ready_line_shows_the_waiting_queue():
    """After a dispatch the remaining queue is logged in dispatch order."""
    gate = threading.Event()
    llm = RecordingLLM(gate=gate)
    queue = Queue()
    scheduler = make_scheduler(llm, queue, aging_interval=10)
    scheduler.logger = RecordingLogger()

    queue.put(FakeSyscall("high_agent", PriorityLevel.HIGH))
    queue.put(FakeSyscall("low_agent", PriorityLevel.LOW))

    scheduler.active = True
    thread = threading.Thread(
        target=scheduler.process_llm_requests, daemon=True
    )
    thread.start()
    try:
        # Hold the first dispatch open so low_agent is still in the ready set
        # when the DONE (and therefore READY) line is emitted.
        assert llm.started.wait(timeout=5), "first dispatch never began"
        gate.set()
        assert wait_until(lambda: len(llm.dispatched) >= 2)
    finally:
        scheduler.active = False
        gate.set()
        thread.join(timeout=5)

    # HIGH was queued first here, so this also re-checks priority ordering.
    assert llm.dispatched == ["high_agent", "low_agent"]

    ready = scheduler.logger.text_for("READY")
    assert ready is not None, "no READY line was logged"
    assert "low_agent" in ready


def test_live_log_survives_a_failed_dispatch():
    """A backend failure is logged and does not kill the scheduler thread."""
    queue = Queue()
    scheduler = make_scheduler(FailingLLM(), queue)
    scheduler.logger = RecordingLogger()

    syscall = FakeSyscall("unlucky_agent", PriorityLevel.NORMAL)
    queue.put(syscall)

    with llm_dispatch_thread(scheduler):
        assert wait_until(lambda: syscall.event.is_set())

    assert "ERROR" in scheduler.logger.tags()
    assert "unlucky_agent" in scheduler.logger.text_for("ERROR")
