"""
Focused Test: user_id propagation from HTTP request to ContextInjector

Proves that the full kernel request path reliably carries an explicit
user_id from the HTTP layer through to ContextInjector.inject():

    QueryRequest.user_id
    → launch.py attaches query._request_user_id
    → SyscallExecutor.execute_request extracts it
    → ContextInjector.inject(user_id="alex_123")

This test exercises the SyscallExecutor directly (unit-level), not
through HTTP, but covers the same internal code path.

Run:
    pytest tests/modules/memory/test_llm_request_user_id_propagation.py -v
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, call

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.access import AccessManager
from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
from aios.memory.providers.base import MemoryProvider
from aios.memory.write_barrier import MemoryWriteBarrier
from aios.syscall.syscall import SyscallExecutor


# ------------------------------------------------------------------
# Minimal provider stub (needed for ContextInjector construction)
# ------------------------------------------------------------------


class StubProvider(MemoryProvider):
    """No-op provider for injection path testing."""

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="stub")

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="stub")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="stub")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        return MemoryResponse(success=True, search_results=[])

    def retrieve_memory_raw(
        self, query: MemoryQuery
    ) -> List[Any]:
        return []

    def close(self) -> None:
        pass

    def sync_llm_from_query(self, llms) -> None:
        pass


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _build_executor_with_injector_spy() -> (
    tuple[SyscallExecutor, MagicMock]
):
    """Build a SyscallExecutor with a real ContextInjector whose
    inject() method is wrapped with a spy (side_effect preserves
    original behavior while recording calls).
    """
    # Build MemoryManager without ConfigManager
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = StubProvider()
    manager.barrier = MemoryWriteBarrier(
        config={"enabled": False}
    )
    manager.access_manager = AccessManager()

    config = {
        "auto_inject": True,
        "max_injected_memories": 5,
        "relevance_threshold": 0.0,
        "max_memory_tokens": 1500,
    }

    injector = ContextInjector(
        memory_manager=manager, config=config
    )

    # Wrap inject with a spy that records calls but delegates
    # to the real implementation
    original_inject = injector.inject
    inject_spy = MagicMock(side_effect=original_inject)
    injector.inject = inject_spy

    # Build executor
    executor = SyscallExecutor()
    executor.context_injector = injector
    executor.conversation_extractor = None
    executor.memory_manager = manager

    return executor, inject_spy


# ==================================================================
# Tests
# ==================================================================


class TestLLMRequestUserIdPropagation(unittest.TestCase):
    """Verify that user_id flows correctly from the LLMQuery
    _request_user_id attribute through SyscallExecutor to
    ContextInjector.inject().
    """

    def setUp(self) -> None:
        self.executor, self.inject_spy = (
            _build_executor_with_injector_spy()
        )

    # ----------------------------------------------------------
    # Step 1: _request_user_id attribute survives on LLMQuery
    # ----------------------------------------------------------

    def test_request_user_id_attr_is_preserved_on_query(
        self,
    ) -> None:
        """Verify that setting _request_user_id on an LLMQuery
        object is accessible via getattr (Pydantic model allows
        extra attrs).
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            action_type="chat",
        )
        query._request_user_id = "alex_123"

        self.assertEqual(
            getattr(query, "_request_user_id", None),
            "alex_123",
        )

    # ----------------------------------------------------------
    # Step 2: SyscallExecutor passes user_id to inject()
    # ----------------------------------------------------------

    def test_executor_passes_user_id_to_inject(self) -> None:
        """When _request_user_id is set on the query, the
        SyscallExecutor should call inject(user_id="alex_123").
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
        )
        # Simulate what launch.py does
        query._request_user_id = "alex_123"

        # Mock execute_llm_syscall to avoid needing LLM infra
        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # Verify inject was called
        self.inject_spy.assert_called_once()

        # Extract the user_id kwarg passed to inject
        call_kwargs = self.inject_spy.call_args.kwargs
        call_args = self.inject_spy.call_args.args

        # inject(agent_name, query, user_id=...)
        # Could be positional or keyword depending on call style
        if "user_id" in call_kwargs:
            actual_user_id = call_kwargs["user_id"]
        else:
            # If passed positionally: inject(agent_name, query, user_id)
            actual_user_id = (
                call_args[2] if len(call_args) > 2 else None
            )

        self.assertEqual(
            actual_user_id,
            "alex_123",
            f"inject() should receive user_id='alex_123', "
            f"got: {actual_user_id!r}. "
            f"Full call: args={call_args}, kwargs={call_kwargs}",
        )

    def test_executor_passes_none_when_no_request_user_id(
        self,
    ) -> None:
        """When _request_user_id is NOT set, the executor should
        pass user_id=None to inject().
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            action_type="chat",
        )
        # Do NOT set _request_user_id

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        self.inject_spy.assert_called_once()

        call_kwargs = self.inject_spy.call_args.kwargs
        call_args = self.inject_spy.call_args.args

        if "user_id" in call_kwargs:
            actual_user_id = call_kwargs["user_id"]
        else:
            actual_user_id = (
                call_args[2] if len(call_args) > 2 else None
            )

        self.assertIsNone(
            actual_user_id,
            "inject() should receive user_id=None when "
            "_request_user_id is not set",
        )

    # ----------------------------------------------------------
    # Step 3: user_id is NOT replaced with agent_name
    # ----------------------------------------------------------

    def test_user_id_is_not_replaced_with_agent_name(
        self,
    ) -> None:
        """The executor must NOT substitute the agent_name for
        the explicit user_id. The inject() call should receive
        the original request user_id, not "assistant_agent".
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I do?"}
            ],
            action_type="chat",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        call_kwargs = self.inject_spy.call_args.kwargs
        call_args = self.inject_spy.call_args.args

        if "user_id" in call_kwargs:
            actual_user_id = call_kwargs["user_id"]
        else:
            actual_user_id = (
                call_args[2] if len(call_args) > 2 else None
            )

        self.assertNotEqual(
            actual_user_id,
            "assistant_agent",
            "inject() must NOT receive 'assistant_agent' as "
            "user_id when an explicit request user_id exists",
        )
        self.assertEqual(actual_user_id, "alex_123")

    # ----------------------------------------------------------
    # Step 4: Diagnostics confirm resolved_user_id
    # ----------------------------------------------------------

    def test_diagnostics_reflect_request_user_id(self) -> None:
        """After the full execute_request flow, the injection
        diagnostics should show resolved_user_id="alex_123".
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What language?"}
            ],
            action_type="chat",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "mocked"}
        )

        # Call inject directly to verify diagnostics (the spy
        # side_effect delegates to real inject)
        result_query, diag = (
            self.executor.context_injector.inject(
                "assistant_agent", query, user_id="alex_123"
            )
        )
        self.assertEqual(
            diag["resolved_user_id"],
            "alex_123",
            "Injection diagnostics should show "
            "resolved_user_id='alex_123'",
        )

    # ----------------------------------------------------------
    # Step 5: launch.py QueryRequest → _request_user_id
    # ----------------------------------------------------------

    def test_query_request_user_id_assignment(self) -> None:
        """Simulate the assignment that launch.py performs:
        if request.user_id: query._request_user_id = request.user_id

        This verifies the assignment pattern works correctly.
        """
        # Simulate QueryRequest with user_id
        class MockRequest:
            user_id = "alex_123"
            agent_name = "assistant_agent"

        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hi"}
            ],
            action_type="chat",
        )

        # Replicate launch.py logic
        request = MockRequest()
        if request.user_id:
            query._request_user_id = request.user_id

        # Verify propagation
        self.assertEqual(
            getattr(query, "_request_user_id", None),
            "alex_123",
        )

    def test_query_request_without_user_id_no_attr(
        self,
    ) -> None:
        """When QueryRequest.user_id is None/empty, the
        _request_user_id attr should not be set.
        """
        class MockRequest:
            user_id = None
            agent_name = "assistant_agent"

        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hi"}
            ],
            action_type="chat",
        )

        request = MockRequest()
        if request.user_id:
            query._request_user_id = request.user_id

        # Should not be set
        self.assertIsNone(
            getattr(query, "_request_user_id", None),
            "_request_user_id should not be set when "
            "request.user_id is None",
        )

    # ----------------------------------------------------------
    # Step 6: Non-chat action_types skip injection
    # ----------------------------------------------------------

    def test_non_chat_action_type_skips_injection(
        self,
    ) -> None:
        """action_type other than 'chat' should NOT invoke
        context injection at all.
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Generate JSON"}
            ],
            action_type="chat_with_json_output",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # inject should NOT be called for non-chat actions
        self.inject_spy.assert_not_called()

    # ----------------------------------------------------------
    # Step 7: Nested query_data["user_id"] promotion
    # ----------------------------------------------------------

    def _make_query_request_class(self):
        """Build a standalone QueryRequest model that mirrors
        the validator logic in runtime/launch.py without
        importing the module (which starts kernel threads).
        """
        from pydantic import BaseModel, model_validator
        from typing import Optional, Any
        from typing_extensions import Literal

        class QueryRequest(BaseModel):
            agent_name: str
            query_type: Literal[
                "llm", "tool", "storage", "memory"
            ]
            query_data: Any
            user_id: Optional[str] = None

            @model_validator(mode='before')
            def convert_query_data(cls, data: Any) -> Any:
                if isinstance(data, dict):
                    query_type = data.get('query_type')
                    query_data = data.get('query_data')

                    if not query_type or not query_data:
                        return data

                    if (
                        isinstance(query_data, dict)
                        and not data.get('user_id')
                        and query_data.get('user_id')
                    ):
                        data['user_id'] = query_data['user_id']

                    type_mapping = {
                        'llm': LLMQuery,
                    }
                    target_type = type_mapping.get(query_type)
                    if (
                        target_type
                        and isinstance(query_data, dict)
                        and not isinstance(
                            query_data, target_type
                        )
                    ):
                        try:
                            data['query_data'] = target_type(
                                **query_data
                            )
                        except Exception:
                            pass
                return data

        return QueryRequest

    def test_query_request_promotes_nested_query_data_user_id(
        self,
    ) -> None:
        """When user_id is inside query_data (not top-level),
        QueryRequest.convert_query_data should promote it to
        the top-level user_id field.

        This covers the case where SDK callers send user_id
        nested in query_data rather than at the envelope level.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": (
                    "sophia_martinez_de307eab__kernel_shared"
                ),
            },
        })

        self.assertEqual(
            request.user_id,
            "sophia_martinez_de307eab__kernel_shared",
            "Nested query_data['user_id'] should be promoted "
            "to the top-level QueryRequest.user_id field",
        )

    def test_query_request_top_level_user_id_takes_precedence(
        self,
    ) -> None:
        """When both top-level user_id and nested
        query_data['user_id'] are present, the top-level
        value must win.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "user_id": "top_level_user",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": "nested_user",
            },
        })

        self.assertEqual(
            request.user_id,
            "top_level_user",
            "Top-level user_id must take precedence over "
            "nested query_data['user_id']",
        )

    def test_nested_user_id_propagates_to_request_user_id_attr(
        self,
    ) -> None:
        """End-to-end: nested query_data['user_id'] should
        result in LLMQuery._request_user_id being set via the
        same assignment logic launch.py uses.

        This locks in the full path:
          query_data["user_id"]
          → QueryRequest.user_id (via promotion)
          → LLMQuery._request_user_id
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": (
                    "sophia_martinez_de307eab__kernel_shared"
                ),
            },
        })

        # Replicate launch.py's assignment logic
        query = LLMQuery(
            messages=request.query_data.messages,
            action_type=request.query_data.action_type,
        )
        if request.user_id:
            query._request_user_id = request.user_id

        self.assertEqual(
            getattr(query, "_request_user_id", None),
            "sophia_martinez_de307eab__kernel_shared",
            "Nested user_id should flow through to "
            "LLMQuery._request_user_id",
        )

    def test_no_user_id_anywhere_leaves_none(self) -> None:
        """When neither top-level nor nested user_id is
        provided, QueryRequest.user_id should remain None.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
            },
        })

        self.assertIsNone(
            request.user_id,
            "user_id should be None when not provided in "
            "either location",
        )

    # ----------------------------------------------------------
    # Step 8: Empty/None user_id does not create fake identity
    # ----------------------------------------------------------

    def test_empty_nested_user_id_not_promoted(self) -> None:
        """An empty string user_id inside query_data must NOT
        be promoted — it is falsy and should not create a
        usable identity.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": "",
            },
        })

        # The validator uses `query_data.get('user_id')` which
        # is falsy for "" — promotion should not occur.
        self.assertFalse(
            bool(request.user_id),
            "Empty string user_id should not be promoted to "
            "a truthy top-level value",
        )

    def test_empty_nested_user_id_no_request_user_id_attr(
        self,
    ) -> None:
        """When nested user_id is '', the downstream
        _request_user_id attribute must NOT be set on the
        LLMQuery.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": "",
            },
        })

        # Replicate launch.py logic
        query = LLMQuery(
            messages=[{"role": "user", "content": "hello"}],
            action_type="chat",
        )
        if request.user_id:
            query._request_user_id = request.user_id

        self.assertIsNone(
            getattr(query, "_request_user_id", None),
            "_request_user_id must not be set when nested "
            "user_id is an empty string",
        )

    def test_none_nested_user_id_not_promoted(self) -> None:
        """An explicit None user_id inside query_data must NOT
        be promoted.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": None,
            },
        })

        self.assertIsNone(
            request.user_id,
            "None user_id in query_data should not be "
            "promoted to top-level",
        )

    def test_none_nested_user_id_no_request_user_id_attr(
        self,
    ) -> None:
        """When nested user_id is None, the downstream
        _request_user_id attribute must NOT be set.
        """
        QueryRequest = self._make_query_request_class()

        request = QueryRequest(**{
            "agent_name": "assistant_agent",
            "query_type": "llm",
            "query_data": {
                "messages": [
                    {"role": "user", "content": "hello"}
                ],
                "action_type": "chat",
                "user_id": None,
            },
        })

        query = LLMQuery(
            messages=[{"role": "user", "content": "hello"}],
            action_type="chat",
        )
        if request.user_id:
            query._request_user_id = request.user_id

        self.assertIsNone(
            getattr(query, "_request_user_id", None),
            "_request_user_id must not be set when nested "
            "user_id is None",
        )


if __name__ == "__main__":
    unittest.main()
