# Tests for round-robin dispatch of individual queued LLM syscalls.

from queue import Empty, Queue
from unittest.mock import Mock, call

import pytest

from aios.hooks.stores.queue import getMessage
from aios.scheduler.rr_scheduler import RRScheduler
from aios.syscall import Syscall


def make_scheduler():
    """Build a scheduler without starting services or worker threads."""
    return RRScheduler(
        llm=Mock(),
        memory_manager=Mock(),
        storage_manager=Mock(),
        tool_manager=Mock(),
        log_mode="console",
        get_llm_syscall=Mock(),
        get_memory_syscall=Mock(),
        get_storage_syscall=Mock(),
        get_tool_syscall=Mock(),
        time_slice=0.05,
    )


@pytest.mark.parametrize("request_count", [0, 1, 2])
def test_dispatches_queued_syscalls_as_single_item_batches(request_count):
    """An individual queue item must reach the batch executor in a list."""
    scheduler = make_scheduler()
    queue = Queue()
    syscalls = [Syscall(f"agent-{i}", None) for i in range(request_count)]
    for syscall in syscalls:
        queue.put(syscall)

    def get_syscall():
        try:
            return getMessage(queue)
        except Empty:
            scheduler.active = False
            raise

    scheduler.get_llm_syscall = get_syscall
    scheduler.active = True
    scheduler.process_llm_requests()

    assert scheduler.llm.execute_llm_syscalls.call_args_list == [
        call([syscall]) for syscall in syscalls
    ]
    assert queue.empty()
    for syscall in syscalls:
        assert syscall.get_status() == "executing"
        assert syscall.get_time_limit() == scheduler.time_slice
        assert syscall.get_start_time() is not None


def test_batch_executor_still_accepts_multiple_syscalls():
    """Keep the existing list-based batch API unchanged."""
    scheduler = make_scheduler()
    syscalls = [Syscall("first", None), Syscall("second", None)]

    scheduler._execute_batch_syscalls(
        syscalls, scheduler.llm.execute_llm_syscalls, "LLM"
    )

    scheduler.llm.execute_llm_syscalls.assert_called_once_with(syscalls)
    for syscall in syscalls:
        assert syscall.get_time_limit() == scheduler.time_slice
        assert syscall.get_status() == "executing"
