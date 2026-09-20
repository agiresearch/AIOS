"""Regression tests for ``RRScheduler``'s LLM request path.

``RRScheduler.process_llm_requests`` used to hand a *single* syscall to
``_execute_batch_syscalls``, which iterates its argument. That raised
``TypeError: 'LLMSyscall' object is not iterable`` inside the processing thread,
so the thread died -- and because nothing then set ``syscall.event``, the
calling agent blocked forever on ``syscall.join()``. Every LLM request through
this scheduler hung.

These tests pin the dispatch contract (a sequence of syscalls, one syscall per
round) so it cannot silently regress.

``RRScheduler`` subclasses the kernel scheduler base, so ``cerebrum`` is a
prerequisite and the module is skipped without it.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from queue import Queue
from typing import Any, List, Optional

import pytest

pytest.importorskip("cerebrum")

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
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.time_limit: Optional[float] = None
        self.response: Any = None
        self.event = threading.Event()

    def set_status(self, value):
        self.status = value

    def get_status(self):
        return self.status

    def set_start_time(self, value):
        self.start_time = value

    def set_end_time(self, value):
        self.end_time = value

    def set_time_limit(self, value):
        self.time_limit = value

    def get_time_limit(self):
        return self.time_limit

    def set_response(self, value):
        self.response = value

    def get_pid(self):
        return id(self)


class RecordingLLM:
    """Stand-in for ``LLMAdapter`` that records each round it is handed."""

    def __init__(self):
        #: One entry per adapter call: the agent names in that round.
        self.rounds: List[List[str]] = []

    def execute_llm_syscalls(self, llm_syscalls):
        # The real adapter iterates its argument, so a bare syscall would blow
        # up here just as it did in the kernel.
        batch = list(llm_syscalls)
        self.rounds.append([syscall.agent_name for syscall in batch])
        for syscall in batch:
            syscall.set_status("done")
            syscall.set_response("ok")
            syscall.set_end_time(time.time())
            syscall.event.set()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def make_scheduler(llm: Any, queue: Queue, time_slice: float = 1.0) -> RRScheduler:
    def getter():
        return queue.get(block=True, timeout=0.05)

    return RRScheduler(
        llm=llm,
        memory_manager=None,
        storage_manager=None,
        tool_manager=None,
        log_mode="console",
        get_llm_syscall=getter,
        get_memory_syscall=None,
        get_storage_syscall=None,
        get_tool_syscall=None,
        time_slice=time_slice,
    )


@contextmanager
def llm_dispatch_thread(scheduler: RRScheduler):
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


# ----------------------------------------------------------------------
# The dispatch contract
# ----------------------------------------------------------------------
def test_a_bare_syscall_is_not_a_valid_round():
    """Documents the bug: the adapter's entry point takes a sequence."""
    scheduler = make_scheduler(RecordingLLM(), Queue())

    with pytest.raises(TypeError):
        scheduler._execute_batch_syscalls(
            FakeSyscall("agent"), RecordingLLM().execute_llm_syscalls, "LLM"
        )


def test_adapter_receives_a_sequence_of_syscalls():
    """Regression: the adapter must be handed an iterable, never one syscall."""
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue)
    queue.put(FakeSyscall("agent", "normal"))

    with llm_dispatch_thread(scheduler):
        assert wait_until(lambda: llm.rounds)

    assert llm.rounds
    for round_agents in llm.rounds:
        assert isinstance(round_agents, list)
    assert llm.rounds[0] == ["agent"]


def test_one_syscall_is_dispatched_per_round():
    """Round robin gives each syscall one slice instead of batching."""
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue)
    for name in ("first", "second", "third"):
        queue.put(FakeSyscall(name, "normal"))

    with llm_dispatch_thread(scheduler):
        assert wait_until(lambda: sum(len(r) for r in llm.rounds) == 3)

    assert llm.rounds[:3] == [["first"], ["second"], ["third"]]


def test_time_slice_is_stamped_on_each_syscall():
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue, time_slice=0.25)
    syscall = FakeSyscall("agent", "normal")
    queue.put(syscall)

    with llm_dispatch_thread(scheduler):
        assert wait_until(lambda: syscall.status == "done")

    assert syscall.get_time_limit() == 0.25


def test_dispatched_syscall_is_completed_and_unblocked():
    """Regression: the agent must not be left waiting on its event.

    Before the fix the processing thread died on the first request, so the
    syscall was never answered and ``syscall.join()`` in ``SyscallExecutor``
    never returned.
    """
    llm = RecordingLLM()
    queue = Queue()
    scheduler = make_scheduler(llm, queue)
    syscall = FakeSyscall("agent", "normal")

    with llm_dispatch_thread(scheduler):
        queue.put(syscall)
        assert wait_until(lambda: syscall.event.is_set())

    assert syscall.status == "done"
    assert syscall.response == "ok"
    assert syscall.start_time is not None
    assert syscall.end_time is not None
