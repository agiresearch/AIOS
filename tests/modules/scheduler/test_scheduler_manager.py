"""Tests for SchedulerManager: choosing a policy and changing it at runtime.

The manager is exercised against the real scheduler classes with injected queue
readers, so the tests do not touch the kernel's global request queues and can
run without a server or a model backend.

The load-bearing test here is
``test_switch_requeues_requests_that_were_accepted_but_not_dispatched``. A
``PriorityScheduler`` can be holding requests it has already taken off the
queue, and every one of those is a thread blocked on ``syscall.join()``. If a
policy switch dropped them, the agents behind them would hang forever -- which
is exactly the failure this manager exists to prevent.
"""

from __future__ import annotations

import threading
import time
from queue import Queue
from typing import Any, List

import pytest

pytest.importorskip("cerebrum")

from aios.scheduler.fifo_scheduler import FIFOScheduler  # noqa: E402
from aios.scheduler.manager import SchedulerManager  # noqa: E402
from aios.scheduler.priority_policy import PriorityLevel  # noqa: E402
from aios.scheduler.priority_scheduler import PriorityScheduler  # noqa: E402
from aios.scheduler.rr_scheduler import RRScheduler  # noqa: E402


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------
class FakeSyscall:
    """Minimal stand-in for ``aios.syscall.Syscall``."""

    def __init__(self, agent_name: str, priority: Any = None):
        self.agent_name = agent_name
        self.priority = priority
        self.status: Any = None
        self.created_time: Any = None
        self.start_time: Any = None
        self.end_time: Any = None
        self.response: Any = None
        self.event = threading.Event()

    def get_priority(self):
        return self.priority

    def get_created_time(self):
        return self.created_time

    def get_start_time(self):
        return self.start_time

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


class GatedLLM:
    """Adapter whose first call blocks until the gate is opened."""

    def __init__(self) -> None:
        self.gate = threading.Event()
        self.started = threading.Event()
        self.dispatched: List[str] = []

    def execute_llm_syscalls(self, llm_syscalls):
        self.started.set()
        self.gate.wait(timeout=10)
        for syscall in llm_syscalls:
            self.dispatched.append(syscall.agent_name)
            syscall.set_status("done")
            syscall.set_response("ok")
            syscall.set_end_time(time.time())
            syscall.event.set()


class IdleLLM:
    """Adapter that completes requests immediately."""

    def execute_llm_syscalls(self, llm_syscalls):
        for syscall in llm_syscalls:
            syscall.set_status("done")
            syscall.set_response("ok")
            syscall.set_end_time(time.time())
            syscall.event.set()


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


def make_manager(
    scheduler_config: dict,
    llm: Any = None,
    llm_queue: Queue | None = None,
    use_context_manager: bool = False,
    released: List[Any] | None = None,
) -> SchedulerManager:
    """Build a manager wired to injected queues so no kernel state is touched."""
    llm_queue = llm_queue if llm_queue is not None else Queue()
    components = {
        "llms": llm if llm is not None else IdleLLM(),
        "memory": FakeManager(),
        "storage": FakeManager(),
        "tool": FakeManager(),
    }
    # Each processor gets its own queue. Sharing one would let the memory,
    # storage or tool thread consume a request meant for the LLM path.
    getters = {
        "get_llm_syscall": make_queue_getter(llm_queue),
        "get_memory_syscall": make_queue_getter(Queue()),
        "get_storage_syscall": make_queue_getter(Queue()),
        "get_tool_syscall": make_queue_getter(Queue()),
    }
    sink = released if released is not None else []
    return SchedulerManager(
        components,
        scheduler_config,
        use_context_manager=use_context_manager,
        queue_getters=getters,
        release_llm_syscall=sink.append,
    )


def wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


# ----------------------------------------------------------------------
# Choosing the initial policy
# ----------------------------------------------------------------------
def test_start_builds_the_configured_policy():
    manager = make_manager({"policy": "priority", "priority": {"aging_interval": 7}})
    scheduler = manager.start()
    try:
        assert isinstance(scheduler, PriorityScheduler)
        assert manager.policy == "priority"
        assert manager.options["aging_interval"] == 7
    finally:
        manager.stop()


@pytest.mark.parametrize(
    "config,use_context,expected_class,expected_name",
    [
        ({}, False, FIFOScheduler, "fifo"),
        ({}, True, RRScheduler, "round_robin"),
        ({"policy": "fcfs"}, False, FIFOScheduler, "fifo"),
        ({"policy": "rr"}, False, RRScheduler, "round_robin"),
        ({"policy": "priority"}, False, PriorityScheduler, "priority"),
    ],
)
def test_start_resolves_aliases_and_the_historical_default(
    config, use_context, expected_class, expected_name
):
    manager = make_manager(config, use_context_manager=use_context)
    scheduler = manager.start()
    try:
        assert isinstance(scheduler, expected_class)
        # ``fcfs`` and ``rr`` are spellings of a policy, not policies of their
        # own, so the reported name is the canonical one.
        assert manager.policy == expected_name
    finally:
        manager.stop()


def test_describe_reports_the_running_policy():
    manager = make_manager({"policy": "priority"})
    manager.start()
    try:
        info = manager.describe()
        assert info["policy"] == "priority"
        assert info["policy_class"] == "PriorityScheduler"
        assert "fifo" in info["available_policies"]
        assert "priority" in info["available_policies"]
    finally:
        manager.stop()


# ----------------------------------------------------------------------
# Switching
# ----------------------------------------------------------------------
def test_switch_replaces_the_running_scheduler():
    manager = make_manager({"policy": "fifo"})
    first = manager.start()
    try:
        result = manager.switch("priority")

        assert result["previous"] == "fifo"
        assert result["policy"] == "priority"
        assert result["released_requests"] == 0
        assert isinstance(manager.scheduler, PriorityScheduler)
        assert manager.scheduler is not first
        # The replaced scheduler must not be left dispatching in the background.
        assert first.active is False
    finally:
        manager.stop()


def test_switch_carries_options_through():
    manager = make_manager({"policy": "fifo"})
    manager.start()
    try:
        manager.switch("priority", {"aging_interval": 3, "default_priority": "low"})
        assert manager.options["aging_interval"] == 3
        assert manager.scheduler.policy.aging_interval == 3
        assert (
            manager.scheduler.policy.default_priority is PriorityLevel.LOW
        )
    finally:
        manager.stop()


def test_switch_back_and_forth():
    manager = make_manager({"policy": "priority"})
    manager.start()
    try:
        assert manager.switch("fifo")["policy"] == "fifo"
        assert manager.policy == "fifo"
        assert manager.switch("round_robin")["policy"] == "round_robin"
        assert manager.policy == "round_robin"
        assert manager.switch("priority")["policy"] == "priority"
        assert manager.policy == "priority"
    finally:
        manager.stop()


def test_unknown_policy_leaves_the_running_scheduler_in_place():
    """A typo must not take the kernel's scheduler down."""
    manager = make_manager({"policy": "fifo"})
    original = manager.start()
    try:
        with pytest.raises(ValueError, match="Unknown scheduling policy"):
            manager.switch("lottery")

        assert manager.policy == "fifo"
        assert manager.scheduler is original
        assert original.active is True
    finally:
        manager.stop()


def test_invalid_option_leaves_the_running_scheduler_in_place():
    """A bad option is caught before the running scheduler is stopped."""
    manager = make_manager({"policy": "fifo"})
    original = manager.start()
    try:
        with pytest.raises(ValueError, match="aging_interval"):
            manager.switch("priority", {"aging_interval": 0})

        assert manager.policy == "fifo"
        assert manager.scheduler is original
        assert original.active is True
    finally:
        manager.stop()


def test_switch_requeues_requests_that_were_accepted_but_not_dispatched():
    """The reason this class exists: a switch must not strand waiting agents.

    The priority scheduler admits requests off the queue into its own ready set.
    With the adapter gated, the first request is dispatched and held while the
    second sits in that ready set. Switching policy must hand the second request
    back, or the agent behind it blocks on ``syscall.join()`` forever.
    """
    llm = GatedLLM()
    llm_queue: Queue = Queue()
    released: List[Any] = []
    manager = make_manager(
        {"policy": "priority"},
        llm=llm,
        llm_queue=llm_queue,
        released=released,
    )
    old_scheduler = manager.start()

    llm_queue.put(FakeSyscall("first_agent", PriorityLevel.HIGH))
    llm_queue.put(FakeSyscall("second_agent", PriorityLevel.LOW))

    try:
        # Both requests admitted; the first is dispatched and blocked on the
        # gate, so the second is parked in the ready set.
        assert llm.started.wait(timeout=5), "no dispatch began"
        assert wait_until(lambda: len(old_scheduler.ready_snapshot()) == 1)

        def release_once_stopped():
            """Let the in-flight call finish only after the switch stopped it.

            ``stop`` clears ``active`` before joining, so once that has
            happened the processing thread will exit instead of dispatching the
            parked request.
            """
            assert wait_until(lambda: old_scheduler.active is False)
            llm.gate.set()

        releaser = threading.Thread(target=release_once_stopped, daemon=True)
        releaser.start()

        result = manager.switch("fifo")
        releaser.join(timeout=5)

        assert result["released_requests"] == 1
        assert [syscall.agent_name for syscall in released] == ["second_agent"]
        # ...and it will be picked up by the new scheduler like any arrival.
        assert isinstance(manager.scheduler, FIFOScheduler)
    finally:
        llm.gate.set()
        manager.stop()
