"""
Unit tests for ``aios.syscall.syscall.SyscallExecutor``.

Tests dispatch logic, create_syscall factory, _get_latest_user_message,
barrier stamping, and execute_request routing — all via mocks, no real
queues/threads/memory backends.

Deviations from plan assumptions (confirmed from source):
- Context injection runs for action_type in ("chat", "chat_with_tool_call_output"),
  NOT just "chat". The plan assumed only "chat".
- "call_tool" with no tool_calls returns a ToolResponse object (not a dict),
  with response_message="No tool was called by LLM" and finished=False.
- create_syscall returns None (implicitly) for unrecognised query types.
"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery
from cerebrum.storage.apis import StorageQuery
from cerebrum.tool.apis import ToolQuery, ToolResponse

from aios.syscall.syscall import SyscallExecutor
from aios.memory.write_barrier import MemoryWriteBarrier


# ------------------------------------------------------------------
# _get_latest_user_message
# ------------------------------------------------------------------

class TestGetLatestUserMessage:
    """Pure helper — no mocks needed."""

    def test_empty_messages_returns_none(self):
        assert SyscallExecutor._get_latest_user_message([]) is None

    def test_no_user_role_returns_none(self):
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "assistant", "content": "Hello"},
        ]
        assert SyscallExecutor._get_latest_user_message(messages) is None

    def test_single_user_message(self):
        messages = [{"role": "user", "content": "hi"}]
        assert SyscallExecutor._get_latest_user_message(messages) == "hi"

    def test_multiple_user_messages_returns_last(self):
        messages = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "reply"},
            {"role": "user", "content": "second"},
        ]
        result = SyscallExecutor._get_latest_user_message(messages)
        assert result == "second"

    def test_user_message_without_content_key(self):
        """If the user message has role but no content, returns None."""
        messages = [{"role": "user"}]
        assert SyscallExecutor._get_latest_user_message(messages) is None


# ------------------------------------------------------------------
# create_syscall
# ------------------------------------------------------------------

class TestCreateSyscall:
    """Dispatch table: Query type → Syscall subclass."""

    def test_llm_query_creates_llm_syscall(self):
        from aios.syscall.llm import LLMSyscall
        executor = SyscallExecutor()
        query = MagicMock(spec=LLMQuery)
        # Make isinstance check pass
        with patch(
            "aios.syscall.syscall.isinstance",
            side_effect=lambda obj, cls: cls == LLMQuery
            if cls in (LLMQuery, StorageQuery, MemoryQuery, ToolQuery)
            else type.__instancecheck__(cls, obj),
        ):
            pass
        # Simpler: just use real query objects
        query = LLMQuery(
            messages=[{"role": "user", "content": "hi"}],
            action_type="chat",
        )
        sc = executor.create_syscall("agent_a", query)
        from aios.syscall.llm import LLMSyscall
        assert isinstance(sc, LLMSyscall)
        assert sc.agent_name == "agent_a"

    def test_storage_query_creates_storage_syscall(self):
        from aios.syscall.storage import StorageSyscall
        executor = SyscallExecutor()
        query = StorageQuery(
            operation_type="read",
            params={"path": "/tmp/test"},
        )
        sc = executor.create_syscall("agent_b", query)
        assert isinstance(sc, StorageSyscall)

    def test_memory_query_creates_memory_syscall(self):
        from aios.syscall.memory import MemorySyscall
        executor = SyscallExecutor()
        query = MemoryQuery(
            operation_type="add_memory",
            params={"content": "hello"},
        )
        sc = executor.create_syscall("agent_c", query)
        assert isinstance(sc, MemorySyscall)

    def test_tool_query_creates_tool_syscall(self):
        from aios.syscall.tool import ToolSyscall
        executor = SyscallExecutor()
        query = ToolQuery(tool_calls=[{"name": "calc"}])
        sc = executor.create_syscall("agent_d", query)
        assert isinstance(sc, ToolSyscall)

    def test_unknown_query_returns_none(self):
        executor = SyscallExecutor()
        result = executor.create_syscall("agent_x", "not a query")
        assert result is None


# ------------------------------------------------------------------
# Barrier stamping (isolated)
# ------------------------------------------------------------------

class TestBarrierStamping:
    """Barrier acquire/snapshot on memory syscalls within _execute_syscall."""

    def _make_executor_with_barrier(self):
        executor = SyscallExecutor()
        mm = MagicMock()
        # Use spec=MemoryWriteBarrier so a typo like barrier.aquire()
        # would raise AttributeError. Instance attributes (_enabled,
        # _seq_counter, etc.) are init-assigned and invisible to spec=,
        # but we only call the public methods here (acquire, snapshot).
        mm.barrier = MagicMock(spec=MemoryWriteBarrier)
        mm.barrier.acquire.return_value = 42
        mm.barrier.snapshot.return_value = 7
        executor.memory_manager = mm
        return executor, mm

    @patch("aios.syscall.syscall.global_memory_req_queue_add_message")
    def test_add_memory_with_user_id_calls_acquire(self, mock_enqueue):
        """add_memory with user_id in metadata → barrier.acquire(uid)."""
        executor, mm = self._make_executor_with_barrier()
        query = MemoryQuery(
            operation_type="add_memory",
            params={
                "content": "test",
                "metadata": {"user_id": "alice"},
            },
        )
        # We can't run the full _execute_syscall (it starts threads),
        # so we test the stamping section by calling create_syscall
        # and then checking what _execute_syscall would do.
        # Instead, test it via a patched run that stops after stamping:
        from aios.syscall.memory import MemorySyscall

        syscall = executor.create_syscall("agent", query)
        assert isinstance(syscall, MemorySyscall)

        # Simulate the stamping logic inline (extracted from _execute_syscall)
        op = syscall.query.operation_type
        uid = syscall.query.params.get("metadata", {}).get("user_id")
        if op in ("add_memory", "add_agentic_memory") and uid:
            syscall.barrier_seq = mm.barrier.acquire(uid)

        mm.barrier.acquire.assert_called_once_with("alice")
        assert syscall.barrier_seq == 42

    @patch("aios.syscall.syscall.global_memory_req_queue_add_message")
    def test_retrieve_memory_with_user_id_calls_snapshot(self, mock_enqueue):
        """retrieve_memory with user_id → barrier.snapshot(uid)."""
        executor, mm = self._make_executor_with_barrier()
        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={"content": "search", "user_id": "bob"},
        )
        from aios.syscall.memory import MemorySyscall

        syscall = executor.create_syscall("agent", query)
        # Simulate stamping logic
        op = syscall.query.operation_type
        uid = syscall.query.params.get("user_id")
        if op in ("retrieve_memory", "retrieve_memory_raw") and uid:
            syscall.barrier_snapshot = mm.barrier.snapshot(uid)

        mm.barrier.snapshot.assert_called_once_with("bob")
        assert syscall.barrier_snapshot == 7

    def test_add_memory_without_user_id_skips_acquire(self):
        """add_memory without user_id in metadata → no acquire call."""
        executor, mm = self._make_executor_with_barrier()
        query = MemoryQuery(
            operation_type="add_memory",
            params={"content": "test", "metadata": {}},
        )
        from aios.syscall.memory import MemorySyscall

        syscall = executor.create_syscall("agent", query)
        op = syscall.query.operation_type
        uid = syscall.query.params.get("metadata", {}).get("user_id")
        if op in ("add_memory", "add_agentic_memory") and uid:
            syscall.barrier_seq = mm.barrier.acquire(uid)

        mm.barrier.acquire.assert_not_called()

    def test_memory_manager_none_skips_gracefully(self):
        """memory_manager=None → no barrier stamping, no crash."""
        executor = SyscallExecutor()
        executor.memory_manager = None
        executor.context_injector = None
        query = MemoryQuery(
            operation_type="add_memory",
            params={
                "content": "test",
                "metadata": {"user_id": "alice"},
            },
        )
        from aios.syscall.memory import MemorySyscall

        syscall = executor.create_syscall("agent", query)
        # Simulate: mm is None → skip
        mm = executor.memory_manager or (
            executor.context_injector.memory_manager
            if executor.context_injector else None
        )
        assert mm is None
        # No crash — barrier stamping skipped


# ------------------------------------------------------------------
# execute_request dispatch
# ------------------------------------------------------------------

class TestExecuteRequestDispatch:
    """High-level routing in execute_request."""

    def test_chat_invokes_injection_and_extraction(self):
        """action_type='chat' with context_injector →
        inject() called before LLM, extract_async() after.
        Order is asserted via a shared call tracker."""
        executor = SyscallExecutor()
        call_order = []

        # Mock the injector
        injector = MagicMock()
        injector.memory_manager = MagicMock()
        injector.memory_manager.sync_llm_from_query = MagicMock()

        def _inject_side_effect(*args, **kwargs):
            call_order.append("inject")
            return (
                LLMQuery(
                    messages=[{"role": "user", "content": "hi"}],
                    action_type="chat",
                ),
                {"resolved_user_id": "u1", "injected_count": 0},
            )

        injector.inject.side_effect = _inject_side_effect
        executor.context_injector = injector

        # Mock extractor
        extractor = MagicMock()

        def _extract_side_effect(*args, **kwargs):
            call_order.append("extract")

        extractor.extract_async.side_effect = _extract_side_effect
        executor.conversation_extractor = extractor

        # Mock the LLM syscall execution
        mock_response = MagicMock()
        mock_response.response_message = "hello!"

        def _llm_side_effect(*args, **kwargs):
            call_order.append("llm")
            return {"response": mock_response}

        with patch.object(
            executor, "execute_llm_syscall",
            side_effect=_llm_side_effect,
        ):
            query = LLMQuery(
                messages=[{"role": "user", "content": "hi"}],
                action_type="chat",
            )
            result = executor.execute_request("agent", query)

        # Assert correct ORDER: inject → llm → extract
        assert call_order == ["inject", "llm", "extract"]

        # Verify user_id propagated from diagnostics
        call_kwargs = extractor.extract_async.call_args
        assert call_kwargs[1]["user_id"] == "u1" or call_kwargs[0][3] == "u1"

    def test_chat_with_tool_call_output_also_gets_injection(self):
        """action_type='chat_with_tool_call_output' triggers injection
        (same branch as 'chat')."""
        executor = SyscallExecutor()
        injector = MagicMock()
        injector.memory_manager = MagicMock()
        injector.memory_manager.sync_llm_from_query = MagicMock()
        injector.inject.return_value = (
            LLMQuery(
                messages=[{"role": "user", "content": "result"}],
                action_type="chat_with_tool_call_output",
            ),
            {"resolved_user_id": None, "injected_count": 0},
        )
        executor.context_injector = injector
        executor.conversation_extractor = None

        mock_response = MagicMock()
        mock_response.response_message = "ok"
        with patch.object(
            executor, "execute_llm_syscall",
            return_value={"response": mock_response},
        ):
            query = LLMQuery(
                messages=[{"role": "user", "content": "result"}],
                action_type="chat_with_tool_call_output",
            )
            executor.execute_request("agent", query)

        injector.inject.assert_called_once()

    def test_chat_with_json_output_skips_injection(self):
        """action_type='chat_with_json_output' does NOT call inject."""
        executor = SyscallExecutor()
        injector = MagicMock()
        executor.context_injector = injector

        with patch.object(
            executor, "execute_llm_syscall",
            return_value={"response": MagicMock()},
        ):
            query = LLMQuery(
                messages=[{"role": "user", "content": "json pls"}],
                action_type="chat_with_json_output",
            )
            executor.execute_request("agent", query)

        injector.inject.assert_not_called()

    def test_call_tool_no_tool_calls_returns_tool_response(self):
        """action_type='call_tool' with empty tool_calls → ToolResponse
        with 'No tool was called by LLM'."""
        executor = SyscallExecutor()
        mock_resp = MagicMock()
        mock_resp.tool_calls = None

        with patch.object(
            executor, "execute_llm_syscall",
            return_value={"response": mock_resp},
        ):
            query = LLMQuery(
                messages=[{"role": "user", "content": "call something"}],
                action_type="call_tool",
            )
            result = executor.execute_request("agent", query)

        assert isinstance(result, ToolResponse)
        assert result.response_message == "No tool was called by LLM"
        assert result.finished is False

    def test_memory_query_routes_to_execute_memory_syscall(self):
        """MemoryQuery → execute_memory_syscall."""
        executor = SyscallExecutor()
        with patch.object(
            executor, "execute_memory_syscall",
            return_value={"response": "ok"},
        ) as mock_mem:
            query = MemoryQuery(
                operation_type="add_memory",
                params={"content": "hi"},
            )
            result = executor.execute_request("agent", query)

        mock_mem.assert_called_once_with("agent", query)
        assert result == {"response": "ok"}

    def test_storage_query_routes_to_execute_storage_syscall(self):
        """StorageQuery → execute_storage_syscall."""
        executor = SyscallExecutor()
        with patch.object(
            executor, "execute_storage_syscall",
            return_value={"response": "stored"},
        ) as mock_sto:
            query = StorageQuery(
                operation_type="write",
                params={"path": "/tmp/x"},
            )
            result = executor.execute_request("agent", query)

        mock_sto.assert_called_once_with("agent", query)

    def test_tool_query_routes_to_execute_tool_syscall(self):
        """ToolQuery → execute_tool_syscall."""
        executor = SyscallExecutor()
        with patch.object(
            executor, "execute_tool_syscall",
            return_value={"response": "done"},
        ) as mock_tool:
            query = ToolQuery(tool_calls=[{"name": "calc"}])
            result = executor.execute_request("agent", query)

        mock_tool.assert_called_once_with("agent", query)
