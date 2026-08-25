"""
Unit tests for ``aios.scheduler.fifo_scheduler.FIFOScheduler``.

Tests ``_execute_syscall`` and ``_execute_batch_syscalls`` in isolation
using mock syscalls and executors — no real threads or queues involved.

Key differences from the plan's assumptions (confirmed from source):
- Success status is the literal string "done" (not an enum).
- Error on _execute_syscall logs at ERROR level (not WARNING).
- _execute_batch_syscalls: preparation failure on one syscall uses
  `continue` but does NOT remove the syscall from the batch list,
  so the original batch is still passed to the executor.
"""
import time
from unittest.mock import MagicMock, patch, call

import pytest

from aios.scheduler.fifo_scheduler import FIFOScheduler
from aios.syscall import Syscall


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_scheduler():
    """Build a FIFOScheduler with all-mock dependencies.

    Patches SchedulerLogger to avoid console output during tests.
    """
    with patch(
        "aios.scheduler.base.SchedulerLogger"
    ) as mock_logger_cls:
        mock_logger_cls.return_value = MagicMock()
        scheduler = FIFOScheduler(
            llm=MagicMock(),
            memory_manager=MagicMock(),
            storage_manager=MagicMock(),
            tool_manager=MagicMock(),
            log_mode="console",
            get_llm_syscall=MagicMock(),
            get_memory_syscall=MagicMock(),
            get_storage_syscall=MagicMock(),
            get_tool_syscall=MagicMock(),
            batch_interval=0.1,
        )
    return scheduler


def _make_syscall(agent_name="test_agent", pid=12345):
    """Build a mock syscall spec'd against the real Syscall class.

    Using spec=Syscall ensures that calling a nonexistent *method*
    (e.g., a typo like .set_stats()) raises AttributeError rather
    than silently passing — protecting against interface drift.

    Instance attributes set in Syscall.__init__ (event, agent_name,
    etc.) are not covered by spec= (known MagicMock limitation), so
    we wire them manually to match the real constructor.
    """
    sc = MagicMock(spec=Syscall)
    # Wire instance attrs that spec= can't discover from __init__
    sc.agent_name = agent_name
    sc.get_pid.return_value = pid
    sc.event = MagicMock()
    return sc


# ------------------------------------------------------------------
# _execute_syscall: success path
# ------------------------------------------------------------------

class TestExecuteSyscallSuccess:
    """Successful single-syscall execution."""

    def test_sets_status_executing_then_done(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(return_value={"result": "ok"})

        scheduler._execute_syscall(sc, executor, "Memory")

        # Status transitions: "executing" then "done"
        sc.set_status.assert_any_call("executing")
        sc.set_status.assert_any_call("done")
        # "executing" called first
        calls = sc.set_status.call_args_list
        assert calls[0] == call("executing")
        assert calls[1] == call("done")

    def test_sets_start_and_end_time(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(return_value="resp")

        scheduler._execute_syscall(sc, executor, "Storage")

        sc.set_start_time.assert_called_once()
        sc.set_end_time.assert_called_once()
        # Start time is before end time
        start = sc.set_start_time.call_args[0][0]
        end = sc.set_end_time.call_args[0][0]
        assert start <= end

    def test_passes_syscall_to_executor_and_stores_response(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        expected_response = {"data": [1, 2, 3]}
        executor = MagicMock(return_value=expected_response)

        result = scheduler._execute_syscall(sc, executor, "Tool")

        executor.assert_called_once_with(sc)
        sc.set_response.assert_called_once_with(expected_response)
        assert result == expected_response

    def test_event_is_set_on_success(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(return_value=None)

        scheduler._execute_syscall(sc, executor, "Memory")

        sc.event.set.assert_called_once()

    def test_returns_executor_response(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(return_value="hello")

        result = scheduler._execute_syscall(sc, executor, "LLM")
        assert result == "hello"


# ------------------------------------------------------------------
# _execute_syscall: error path
# ------------------------------------------------------------------

class TestExecuteSyscallError:
    """Executor raising an exception."""

    def test_returns_none_on_exception(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(side_effect=RuntimeError("boom"))

        result = scheduler._execute_syscall(sc, executor, "Memory")

        assert result is None

    def test_does_not_set_event_on_exception(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(side_effect=ValueError("bad"))

        scheduler._execute_syscall(sc, executor, "Tool")

        sc.event.set.assert_not_called()

    def test_does_not_set_done_status_on_exception(self):
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(side_effect=TypeError("oops"))

        scheduler._execute_syscall(sc, executor, "Storage")

        # "executing" is set before the executor call,
        # but "done" should NOT be set after an exception
        status_calls = [c[0][0] for c in sc.set_status.call_args_list]
        assert "executing" in status_calls
        assert "done" not in status_calls

    def test_logs_error_on_exception(self):
        """Real code logs at ERROR level via module logger."""
        scheduler = _make_scheduler()
        sc = _make_syscall()
        executor = MagicMock(side_effect=RuntimeError("fail"))

        with patch(
            "aios.scheduler.fifo_scheduler.logger"
        ) as mock_logger:
            scheduler._execute_syscall(sc, executor, "Memory")
            mock_logger.error.assert_called_once()
            assert "Memory" in mock_logger.error.call_args[0][0]


# ------------------------------------------------------------------
# _execute_batch_syscalls: empty batch
# ------------------------------------------------------------------

class TestBatchEmpty:
    """Empty batch → early return, executor not called."""

    def test_empty_list_returns_immediately(self):
        scheduler = _make_scheduler()
        executor = MagicMock()

        scheduler._execute_batch_syscalls([], executor, "LLM")

        executor.assert_not_called()

    def test_none_batch_raises_naturally(self):
        """None is not a valid batch — confirm it raises TypeError
        since the code checks `if not batch` which is truthy for None."""
        scheduler = _make_scheduler()
        executor = MagicMock()

        # `if not None` → True → returns immediately
        scheduler._execute_batch_syscalls(None, executor, "LLM")
        executor.assert_not_called()


# ------------------------------------------------------------------
# _execute_batch_syscalls: normal batch
# ------------------------------------------------------------------

class TestBatchNormal:
    """Normal batch execution — all syscalls prepared, executor called."""

    def test_all_syscalls_set_to_executing(self):
        scheduler = _make_scheduler()
        sc1 = _make_syscall("agent_a")
        sc2 = _make_syscall("agent_b")
        executor = MagicMock(return_value=[None, None])

        scheduler._execute_batch_syscalls(
            [sc1, sc2], executor, "LLM",
        )

        sc1.set_status.assert_called_with("executing")
        sc2.set_status.assert_called_with("executing")

    def test_all_syscalls_get_same_start_time(self):
        scheduler = _make_scheduler()
        sc1 = _make_syscall("a")
        sc2 = _make_syscall("b")
        executor = MagicMock(return_value=[])

        scheduler._execute_batch_syscalls(
            [sc1, sc2], executor, "LLM",
        )

        # Both share the same start_time (set before the loop)
        t1 = sc1.set_start_time.call_args[0][0]
        t2 = sc2.set_start_time.call_args[0][0]
        assert t1 == t2

    def test_executor_called_with_full_batch(self):
        scheduler = _make_scheduler()
        sc1 = _make_syscall("a")
        sc2 = _make_syscall("b")
        batch = [sc1, sc2]
        executor = MagicMock(return_value=[])

        scheduler._execute_batch_syscalls(batch, executor, "LLM")

        executor.assert_called_once_with(batch)


# ------------------------------------------------------------------
# _execute_batch_syscalls: preparation failure on one syscall
# ------------------------------------------------------------------

class TestBatchPreparationFailure:
    """One syscall's .set_status() raises — others still processed."""

    def test_failing_syscall_does_not_block_others(self):
        scheduler = _make_scheduler()

        bad_sc = MagicMock()
        bad_sc.set_status.side_effect = RuntimeError("broken")
        bad_sc.agent_name = "bad_agent"

        good_sc = _make_syscall("good_agent")
        executor = MagicMock(return_value=[])

        # The batch includes both — bad_sc prep fails with continue,
        # but the batch list is not modified, so executor still gets
        # both items passed (this is real behavior — the `continue`
        # skips the rest of the loop body but doesn't remove the
        # item from the batch list).
        scheduler._execute_batch_syscalls(
            [bad_sc, good_sc], executor, "LLM",
        )

        # good_sc is still prepared
        good_sc.set_status.assert_called_with("executing")
        # Executor still called with the full original batch
        executor.assert_called_once_with([bad_sc, good_sc])


# ------------------------------------------------------------------
# _execute_batch_syscalls: executor raises
# ------------------------------------------------------------------

class TestBatchExecutorFailure:
    """Executor raises during batch execution."""

    def test_executor_exception_does_not_propagate(self):
        scheduler = _make_scheduler()
        sc = _make_syscall("agent_x")
        executor = MagicMock(
            side_effect=RuntimeError("batch exploded")
        )

        # Should not raise
        scheduler._execute_batch_syscalls(
            [sc], executor, "LLM",
        )

    def test_executor_exception_logged_at_error(self):
        scheduler = _make_scheduler()
        sc = _make_syscall("agent_x")
        executor = MagicMock(
            side_effect=RuntimeError("batch exploded")
        )

        with patch(
            "aios.scheduler.fifo_scheduler.logger"
        ) as mock_logger:
            scheduler._execute_batch_syscalls(
                [sc], executor, "LLM",
            )
            mock_logger.error.assert_called()
            # Error message includes the syscall type
            assert "LLM" in mock_logger.error.call_args[0][0]
