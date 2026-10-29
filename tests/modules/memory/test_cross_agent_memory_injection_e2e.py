"""
End-to-End Test: Cross-Agent Shared Memory Injection

Proves the full integration path for cross-agent memory injection:

    1. ProfileAgent writes shared memory for user_id="alex_123"
    2. TaskAgent writes shared memory for user_id="alex_123"
    3. AssistantAgent calls llm_chat with user_id="alex_123"
    4. Kernel auto_inject retrieves shared memories from both agents
    5. AssistantAgent prompt receives injected personalized context

Unlike the unit-level test_context_injector_explicit_user_id.py,
this test exercises the full SyscallExecutor.execute_request() path
(the same path real agents use), with the LLM call mocked at the
lowest possible point.

Run:
    pytest tests/modules/memory/test_cross_agent_memory_injection_e2e.py -v
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.access import AccessManager
from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
from aios.memory.note import MemoryNote
from aios.memory.providers.base import MemoryProvider
from aios.memory.write_barrier import MemoryWriteBarrier
from aios.syscall.syscall import SyscallExecutor


# ------------------------------------------------------------------
# Test memory provider with cross-agent awareness
# ------------------------------------------------------------------


class CrossAgentTestProvider(MemoryProvider):
    """Provider that stores memories by user_id and supports
    cross-agent shared retrieval with sharing_policy filtering.

    Tracks all retrieve calls for assertion purposes.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[dict]] = {}
        self.retrieve_calls: List[dict] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def seed(
        self,
        content: str,
        metadata: dict,
    ) -> None:
        """Directly seed a memory (bypasses add_memory flow)."""
        user_id = metadata.get("user_id", "unknown")
        self._store.setdefault(user_id, []).append({
            "content": content,
            "metadata": dict(metadata),
            "score": 0.90,
        })

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        metadata = getattr(memory_note, "metadata", {}) or {}
        user_id = metadata.get("user_id", "unknown")
        content = getattr(memory_note, "content", "")
        self._store.setdefault(user_id, []).append({
            "content": content,
            "metadata": dict(metadata),
            "score": 0.90,
        })
        return MemoryResponse(
            success=True, memory_id=f"mem-{id(memory_note)}"
        )

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="ok")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="stub")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Retrieve memories with user_id and sharing_policy
        filtering, mimicking real provider behavior."""
        params = query.params or {}
        user_id = params.get("user_id")
        agent_name = params.get("agent_name")
        sharing_policy = params.get("sharing_policy")

        self.retrieve_calls.append({
            "user_id": user_id,
            "agent_name": agent_name,
            "sharing_policy": sharing_policy,
            "params": dict(params),
        })

        if not user_id:
            return MemoryResponse(
                success=True, search_results=[]
            )

        results = []
        for item in self._store.get(user_id, []):
            meta = item.get("metadata", {})

            # sharing_policy filter: for shared retrieval,
            # only return memories matching the policy
            if sharing_policy:
                if meta.get("sharing_policy") != sharing_policy:
                    continue

            # For own-retrieval (no sharing_policy filter),
            # scope by agent_name (owner_agent)
            if agent_name and not sharing_policy:
                if meta.get("owner_agent") != agent_name:
                    continue

            results.append({
                "content": item["content"],
                "metadata": dict(meta),
                "score": item.get("score", 0.90),
                "keywords": [],
                "tags": [],
                "category": "Uncategorized",
                "timestamp": "",
            })

        return MemoryResponse(
            success=True, search_results=results
        )

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


def _build_executor(
    provider: CrossAgentTestProvider,
) -> tuple[SyscallExecutor, MemoryManager]:
    """Build a SyscallExecutor wired with a real ContextInjector
    and the test provider. The LLM execution is left as a mock
    placeholder.
    """
    # Build MemoryManager without ConfigManager
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    manager.barrier = MemoryWriteBarrier(
        config={"enabled": False}
    )
    # Profile and task agents admit the assistant agent to their
    # privilege groups, as in memory.access_control of config.yaml.
    manager.access_manager = AccessManager({
        "profile_agent": ["assistant_agent"],
        "task_agent": ["assistant_agent"],
    })

    # Build ContextInjector with auto_inject enabled
    config = {
        "auto_inject": True,
        "max_injected_memories": 10,
        "relevance_threshold": 0.0,
        "max_memory_tokens": 3000,
    }
    injector = ContextInjector(
        memory_manager=manager, config=config
    )

    # Build executor and wire components
    executor = SyscallExecutor()
    executor.context_injector = injector
    executor.conversation_extractor = None
    executor.memory_manager = manager

    return executor, manager


# ==================================================================
# End-to-End Tests
# ==================================================================


class TestCrossAgentMemoryInjectionE2E(unittest.TestCase):
    """End-to-end test proving that when AssistantAgent makes an
    LLM chat request with user_id="alex_123", the kernel injects
    shared memories from ProfileAgent and TaskAgent into the
    prompt.
    """

    def setUp(self) -> None:
        self.provider = CrossAgentTestProvider()

        # --- Simulate ProfileAgent writing shared memory ---
        self.provider.seed(
            content="User likes Python and prefers dark mode",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        # --- Simulate TaskAgent writing shared memory ---
        self.provider.seed(
            content="User is working on tax app",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "task_agent",
                "sharing_policy": "shared",
                "memory_type": "task_context",
            },
        )

        # --- Simulate AssistantAgent's own private memory ---
        self.provider.seed(
            content="Previous chat about weather forecast",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )

        self.executor, self.manager = _build_executor(
            self.provider
        )

    # ----------------------------------------------------------
    # Core E2E test: full execute_request path
    # ----------------------------------------------------------

    def test_full_execute_request_injects_cross_agent_memories(
        self,
    ) -> None:
        """Exercise SyscallExecutor.execute_request() with a chat
        LLM query carrying _request_user_id="alex_123".

        The LLM call is mocked, but everything upstream
        (context injection, shared retrieval, formatting) runs
        for real.
        """
        # Build the LLM query as the kernel would
        query = LLMQuery(
            messages=[
                {
                    "role": "user",
                    "content": (
                        "What programming language do I prefer "
                        "and what am I working on?"
                    ),
                }
            ],
            action_type="chat",
            message_return_type="text",
        )
        # Simulate what launch.py does: attach per-request
        # user_id
        query._request_user_id = "alex_123"

        # Mock the LLM execution (we only care about the
        # injected prompt, not the model response)
        captured_query = {}

        def mock_execute_llm(agent_name, q):
            # Capture the query AFTER injection has run
            captured_query["messages"] = list(q.messages)
            return {"response": "Mocked LLM response"}

        self.executor.execute_llm_syscall = mock_execute_llm

        # Execute the full request path
        result = self.executor.execute_request(
            "assistant_agent", query
        )

        # Verify LLM was called
        self.assertIn("messages", captured_query)

        # Extract the injected system message
        messages = captured_query["messages"]
        system_messages = [
            m for m in messages if m.get("role") == "system"
        ]
        self.assertGreater(
            len(system_messages), 0,
            "A system message with memory context should be "
            "injected",
        )

        injected_content = system_messages[0]["content"]

        # Assert ProfileAgent's shared memory is injected
        self.assertIn(
            "Python",
            injected_content,
            f"Profile memory about Python should be in "
            f"injected prompt. Got: {injected_content!r}",
        )

        # Assert TaskAgent's shared memory is injected
        self.assertIn(
            "tax app",
            injected_content,
            f"Task memory about tax app should be in "
            f"injected prompt. Got: {injected_content!r}",
        )

    def test_injected_prompt_contains_memory_context_header(
        self,
    ) -> None:
        """The injected system message should include the
        MEMORY CONTEXT delimiters."""
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Tell me about me"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "alex_123"

        captured_query = {}

        def mock_execute_llm(agent_name, q):
            captured_query["messages"] = list(q.messages)
            return {"response": "Mocked"}

        self.executor.execute_llm_syscall = mock_execute_llm
        self.executor.execute_request(
            "assistant_agent", query
        )

        messages = captured_query["messages"]
        system_content = messages[0]["content"]

        self.assertIn(
            "MEMORY CONTEXT", system_content,
            "Injected message should include MEMORY CONTEXT "
            "header",
        )
        self.assertIn(
            "END MEMORY CONTEXT", system_content,
            "Injected message should include "
            "END MEMORY CONTEXT footer",
        )

    # ----------------------------------------------------------
    # Verify user_id scoping
    # ----------------------------------------------------------

    def test_retrieval_uses_alex_123_not_assistant_agent(
        self,
    ) -> None:
        """The provider's retrieve_memory calls should use
        user_id="alex_123", not "assistant_agent".
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # Check all retrieve calls
        retrieve_user_ids = [
            call["user_id"]
            for call in self.provider.retrieve_calls
        ]

        # "alex_123" should be used
        self.assertIn(
            "alex_123",
            retrieve_user_ids,
            f"Retrieval should use user_id='alex_123'. "
            f"Calls: {self.provider.retrieve_calls}",
        )

        # "assistant_agent" should NOT be used as user_id
        self.assertNotIn(
            "assistant_agent",
            retrieve_user_ids,
            f"'assistant_agent' must NOT be used as user_id. "
            f"Calls: {self.provider.retrieve_calls}",
        )

    def test_shared_retrieval_requests_shared_policy(
        self,
    ) -> None:
        """The cross-agent retrieval should explicitly request
        sharing_policy="shared" to filter results."""
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I do?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # Find shared retrieval calls
        shared_calls = [
            c for c in self.provider.retrieve_calls
            if c.get("sharing_policy") == "shared"
        ]
        self.assertGreater(
            len(shared_calls), 0,
            "At least one retrieval should request "
            "sharing_policy='shared'",
        )

    # ----------------------------------------------------------
    # Verify own-memory retrieval is separate
    # ----------------------------------------------------------

    def test_own_memory_retrieval_scoped_by_agent_name(
        self,
    ) -> None:
        """The own-memory retrieval pass should include
        agent_name for ownership scoping."""
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What did we chat?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # Find own-memory calls (agent_name set, no
        # sharing_policy)
        own_calls = [
            c for c in self.provider.retrieve_calls
            if (
                c.get("agent_name") == "assistant_agent"
                and c.get("sharing_policy") is None
            )
        ]
        self.assertGreater(
            len(own_calls), 0,
            "Should have an own-memory retrieval call with "
            "agent_name='assistant_agent'",
        )

    # ----------------------------------------------------------
    # Verify no injection when user_id is absent
    # ----------------------------------------------------------

    def test_no_shared_injection_without_user_id(self) -> None:
        """When no _request_user_id is set, shared memories
        should NOT be injected (only own-agent memories via
        agent_name fallback).
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        # Do NOT set _request_user_id

        captured_query = {}

        def mock_execute_llm(agent_name, q):
            captured_query["messages"] = list(q.messages)
            return {"response": "Mocked"}

        self.executor.execute_llm_syscall = mock_execute_llm
        self.executor.execute_request(
            "assistant_agent", query
        )

        messages = captured_query["messages"]

        # Check if any system message was injected
        system_messages = [
            m for m in messages if m.get("role") == "system"
        ]

        if system_messages:
            content = system_messages[0]["content"]
            # Should NOT contain cross-agent shared content
            # (profile_agent or task_agent memories)
            # Only own-agent memories could be here
            self.assertNotIn(
                "tax app",
                content,
                "Without user_id, TaskAgent's shared memory "
                "should NOT be injected",
            )

    # ----------------------------------------------------------
    # Multiple users don't cross-contaminate
    # ----------------------------------------------------------

    def test_different_user_does_not_get_alex_memories(
        self,
    ) -> None:
        """A request for user_id="bob_456" should NOT receive
        alex_123's memories.
        """
        # Seed a memory for bob_456
        self.provider.seed(
            content="Bob prefers Java",
            metadata={
                "user_id": "bob_456",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "bob_456"

        captured_query = {}

        def mock_execute_llm(agent_name, q):
            captured_query["messages"] = list(q.messages)
            return {"response": "Mocked"}

        self.executor.execute_llm_syscall = mock_execute_llm
        self.executor.execute_request(
            "assistant_agent", query
        )

        messages = captured_query["messages"]
        system_messages = [
            m for m in messages if m.get("role") == "system"
        ]

        if system_messages:
            content = system_messages[0]["content"]
            # Bob should get his own memories
            self.assertIn(
                "Java",
                content,
                "Bob should see his own profile memory",
            )
            # Bob should NOT see Alex's memories
            self.assertNotIn(
                "Python",
                content,
                "Bob should NOT see Alex's Python memory",
            )
            self.assertNotIn(
                "tax app",
                content,
                "Bob should NOT see Alex's tax app memory",
            )

    # ----------------------------------------------------------
    # Verify response is returned correctly
    # ----------------------------------------------------------

    def test_execute_request_returns_llm_response(self) -> None:
        """The execute_request call should return the mocked
        LLM response after injection completes."""
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = "alex_123"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={
                "response": "I see you like Python!"
            }
        )

        result = self.executor.execute_request(
            "assistant_agent", query
        )

        self.assertEqual(
            result["response"],
            "I see you like Python!",
        )

    # ----------------------------------------------------------
    # Negative tests: unsafe identity behavior
    # ----------------------------------------------------------

    def test_no_shared_retrieval_call_without_user_id(
        self,
    ) -> None:
        """When user_id is absent, no retrieval call should
        be made with sharing_policy="shared". The injector
        must not attempt cross-agent shared retrieval.
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        # No _request_user_id set

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # There must be ZERO calls with sharing_policy="shared"
        shared_calls = [
            c for c in self.provider.retrieve_calls
            if c.get("sharing_policy") == "shared"
        ]
        self.assertEqual(
            len(shared_calls), 0,
            f"Without user_id, no shared retrieval should "
            f"occur. Found shared calls: {shared_calls}",
        )

    def test_empty_string_user_id_treated_as_absent(
        self,
    ) -> None:
        """An empty string user_id should be treated the same
        as None — no shared memory retrieval triggered.
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        query._request_user_id = ""

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # No shared retrieval calls should exist
        shared_calls = [
            c for c in self.provider.retrieve_calls
            if c.get("sharing_policy") == "shared"
        ]
        self.assertEqual(
            len(shared_calls), 0,
            f"Empty string user_id should not trigger shared "
            f"retrieval. Found: {shared_calls}",
        )

        # Verify retrieval used agent_name fallback (not "")
        retrieve_user_ids = [
            c["user_id"] for c in self.provider.retrieve_calls
        ]
        self.assertNotIn(
            "",
            retrieve_user_ids,
            "Empty string should never be used as user_id",
        )

    def test_agent_name_never_in_shared_retrieval_user_id(
        self,
    ) -> None:
        """Across multiple requests with and without user_id,
        "assistant_agent" must NEVER appear as user_id in a
        shared retrieval call (sharing_policy="shared").
        """
        # Request 1: with explicit user_id
        q1 = LLMQuery(
            messages=[
                {"role": "user", "content": "Request 1"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        q1._request_user_id = "alex_123"

        # Request 2: without user_id
        q2 = LLMQuery(
            messages=[
                {"role": "user", "content": "Request 2"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        # No _request_user_id

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", q1
        )
        self.executor.execute_request(
            "assistant_agent", q2
        )

        # Inspect all shared retrieval calls
        shared_calls = [
            c for c in self.provider.retrieve_calls
            if c.get("sharing_policy") == "shared"
        ]

        for call in shared_calls:
            self.assertNotEqual(
                call["user_id"],
                "assistant_agent",
                f"'assistant_agent' must NEVER be the user_id "
                f"in a shared retrieval call. Call: {call}",
            )

    def test_user_id_equal_to_agent_name_does_not_trigger_shared(
        self,
    ) -> None:
        """If user_id equals the agent_name (pathological case),
        shared retrieval should NOT be triggered because
        _resolve_user_id returns None for this case.
        """
        query = LLMQuery(
            messages=[
                {"role": "user", "content": "What do I like?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        # Set user_id to the agent name itself
        query._request_user_id = "assistant_agent"

        self.executor.execute_llm_syscall = MagicMock(
            return_value={"response": "Mocked"}
        )

        self.executor.execute_request(
            "assistant_agent", query
        )

        # No shared retrieval should occur
        shared_calls = [
            c for c in self.provider.retrieve_calls
            if c.get("sharing_policy") == "shared"
        ]
        self.assertEqual(
            len(shared_calls), 0,
            f"user_id=agent_name should not trigger shared "
            f"retrieval. Found: {shared_calls}",
        )

    def test_cross_user_isolation_bidirectional(self) -> None:
        """Neither user should see the other's memories when
        requests are made sequentially.
        """
        # Seed memory for jordan_456
        self.provider.seed(
            content="Jordan prefers Go",
            metadata={
                "user_id": "jordan_456",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        # Request for alex_123
        q1 = LLMQuery(
            messages=[
                {"role": "user", "content": "My language?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        q1._request_user_id = "alex_123"

        captured_1 = {}

        def mock_llm_1(agent_name, q):
            captured_1["messages"] = list(q.messages)
            return {"response": "Mocked"}

        self.executor.execute_llm_syscall = mock_llm_1
        self.executor.execute_request(
            "assistant_agent", q1
        )

        # Request for jordan_456
        q2 = LLMQuery(
            messages=[
                {"role": "user", "content": "My language?"}
            ],
            action_type="chat",
            message_return_type="text",
        )
        q2._request_user_id = "jordan_456"

        captured_2 = {}

        def mock_llm_2(agent_name, q):
            captured_2["messages"] = list(q.messages)
            return {"response": "Mocked"}

        self.executor.execute_llm_syscall = mock_llm_2
        self.executor.execute_request(
            "assistant_agent", q2
        )

        # Alex's prompt should have Python, not Go
        sys_1 = [
            m for m in captured_1["messages"]
            if m.get("role") == "system"
        ]
        content_1 = sys_1[0]["content"] if sys_1 else ""
        self.assertIn("Python", content_1)
        self.assertNotIn(
            "Go",
            content_1,
            "Alex should NOT see Jordan's Go memory",
        )

        # Jordan's prompt should have Go, not Python
        sys_2 = [
            m for m in captured_2["messages"]
            if m.get("role") == "system"
        ]
        content_2 = sys_2[0]["content"] if sys_2 else ""
        self.assertIn("Go", content_2)
        self.assertNotIn(
            "Python",
            content_2,
            "Jordan should NOT see Alex's Python memory",
        )


if __name__ == "__main__":
    unittest.main()
