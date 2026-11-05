"""
Regression Test: Explicit user_id injection in ContextInjector

Proves the bug: when AssistantAgent calls llm_chat with an explicit
user_id, the ContextInjector should use that user_id to retrieve
shared memories from other agents (ProfileAgent, TaskAgent) instead
of falling back to "assistant_agent" as the memory scope.

The scenario:
    1. ProfileAgent writes a shared memory with user_id="alex_123"
    2. TaskAgent writes a shared memory with user_id="alex_123"
    3. AssistantAgent makes an LLM chat request with user_id="alex_123"
    4. ContextInjector should retrieve shared memories for "alex_123"
    5. ContextInjector should NOT use "assistant_agent" as user_id

This test is expected to FAIL before the fix and PASS after.

Run:
    pytest tests/modules/memory/test_context_injector_explicit_user_id.py -v
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
from typing import Any, Dict, List
from unittest.mock import patch

# Ensure project root on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
from aios.memory.note import MemoryNote
from aios.memory.providers.base import MemoryProvider
from aios.memory.write_barrier import MemoryWriteBarrier

from tests.modules.memory._doubles.open_access import (
    personalization_access_manager,
)


# ------------------------------------------------------------------
# Test memory provider that tracks retrieval user_ids
# ------------------------------------------------------------------


class TrackingMemoryProvider(MemoryProvider):
    """A deterministic provider that:
    1. Stores memories by user_id
    2. Tracks which user_ids were used in retrieve calls
    3. Respects sharing_policy for cross-agent retrieval
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[dict]] = {}
        self.retrieve_calls: List[dict] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def seed_memory(
        self,
        content: str,
        metadata: dict,
    ) -> None:
        """Directly seed a memory into the store (bypasses
        add_memory flow for test setup convenience)."""
        user_id = metadata.get("user_id", "unknown")
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.92,
        }
        self._store.setdefault(user_id, []).append(mem)

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        metadata = getattr(memory_note, "metadata", {}) or {}
        user_id = metadata.get("user_id", "unknown")
        content = getattr(memory_note, "content", "")
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.92,
        }
        self._store.setdefault(user_id, []).append(mem)
        return MemoryResponse(
            success=True, memory_id=f"mem-{id(mem)}"
        )

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="ok")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not impl")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Return memories scoped to user_id in query.params.

        Also records which user_id was used for each call so
        tests can assert the correct scoping.
        """
        params = query.params or {}
        user_id = params.get("user_id")
        agent_name = params.get("agent_name")
        sharing_policy = params.get("sharing_policy")

        # Track this call for assertions
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
            item_meta = item.get("metadata", {})

            # If sharing_policy filter is requested, only
            # return memories matching that policy
            if sharing_policy:
                if item_meta.get("sharing_policy") != sharing_policy:
                    continue

            # If agent_name filter is set and no sharing_policy
            # filter, return only that agent's memories (own
            # retrieval). If sharing_policy is set, skip agent
            # filter (cross-agent retrieval).
            if agent_name and not sharing_policy:
                if item_meta.get("owner_agent") != agent_name:
                    continue

            results.append({
                "content": item["content"],
                "metadata": item_meta,
                "score": item.get("score", 0.92),
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


def _build_injector_with_provider(
    provider: TrackingMemoryProvider,
) -> ContextInjector:
    """Create a ContextInjector with a real MemoryManager backed by
    our tracking provider. Write barrier is disabled to avoid
    blocking.
    """
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    manager.barrier = MemoryWriteBarrier(
        config={"enabled": False}
    )
    manager.access_manager = personalization_access_manager()

    config = {
        "auto_inject": True,
        "max_injected_memories": 10,
        "relevance_threshold": 0.0,
        "max_memory_tokens": 3000,
    }

    injector = ContextInjector(
        memory_manager=manager, config=config
    )
    return injector


def _make_llm_query(user_message: str) -> LLMQuery:
    """Build a minimal LLMQuery with a user message."""
    return LLMQuery(
        messages=[{"role": "user", "content": user_message}],
        tools=None,
        action_type="chat",
        message_return_type="text",
    )


# ==================================================================
# Regression tests
# ==================================================================


class TestContextInjectorExplicitUserId(unittest.TestCase):
    """Regression test: explicit user_id in inject() should be
    used to scope memory retrieval to the correct end-user,
    not the agent name.
    """

    def setUp(self) -> None:
        self.provider = TrackingMemoryProvider()

        # Seed shared memories from ProfileAgent
        self.provider.seed_memory(
            content="User likes Python and prefers dark mode",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        # Seed shared memories from TaskAgent
        self.provider.seed_memory(
            content="User is working on tax app",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "task_agent",
                "sharing_policy": "shared",
                "memory_type": "task_context",
            },
        )

        # Seed a private memory from assistant_agent (should
        # NOT show up in shared retrieval, only own retrieval)
        self.provider.seed_memory(
            content="Previous conversation about weather",
            metadata={
                "user_id": "alex_123",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )

        self.injector = _build_injector_with_provider(
            self.provider
        )

    # ----------------------------------------------------------
    # Core regression test
    # ----------------------------------------------------------

    def test_inject_uses_explicit_user_id_for_retrieval(
        self,
    ) -> None:
        """When inject() is called with user_id="alex_123",
        it should retrieve shared memories using "alex_123"
        as the scope, NOT "assistant_agent".
        """
        query = _make_llm_query(
            "What programming language do I prefer?"
        )

        result_query, diagnostics = self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id="alex_123",
        )

        # Verify resolved_user_id is alex_123
        self.assertEqual(
            diagnostics["resolved_user_id"],
            "alex_123",
            "resolved_user_id should be 'alex_123', not None "
            "or 'assistant_agent'",
        )

    def test_shared_memories_from_other_agents_are_injected(
        self,
    ) -> None:
        """Shared memories from profile_agent and task_agent
        should be retrieved and injected into the LLM context.
        """
        query = _make_llm_query(
            "What programming language do I prefer?"
        )

        result_query, diagnostics = self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id="alex_123",
        )

        # Memories should have been injected
        self.assertGreater(
            diagnostics["injected_count"],
            0,
            "At least one memory should be injected",
        )

        # Check that source_agents includes the cross-agent
        # sources
        source_agents = diagnostics["source_agents"]
        self.assertIn(
            "profile_agent",
            source_agents,
            f"profile_agent should be in source_agents, "
            f"got: {source_agents}",
        )
        self.assertIn(
            "task_agent",
            source_agents,
            f"task_agent should be in source_agents, "
            f"got: {source_agents}",
        )

        # Verify injected content includes shared memories
        # The injected memories are prepended as a system message
        self.assertGreater(
            len(result_query.messages), 1,
            "A system message should be prepended with memories",
        )

        injected_content = result_query.messages[0]["content"]
        self.assertIn(
            "Python",
            injected_content,
            f"Profile memory about Python should be injected. "
            f"Got: {injected_content!r}",
        )
        self.assertIn(
            "tax app",
            injected_content,
            f"Task memory about tax app should be injected. "
            f"Got: {injected_content!r}",
        )

    def test_retrieval_not_scoped_to_agent_name(
        self,
    ) -> None:
        """The provider's retrieve_memory should NOT be called
        with user_id="assistant_agent". It should use
        "alex_123" for both own and shared retrieval.
        """
        query = _make_llm_query(
            "What programming language do I prefer?"
        )

        self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id="alex_123",
        )

        # Examine which user_ids were used in retrieve calls
        retrieve_user_ids = [
            call["user_id"]
            for call in self.provider.retrieve_calls
        ]

        # "assistant_agent" should NOT be used as user_id
        self.assertNotIn(
            "assistant_agent",
            retrieve_user_ids,
            f"'assistant_agent' should NOT be used as user_id "
            f"for memory retrieval. Calls made: "
            f"{self.provider.retrieve_calls}",
        )

        # "alex_123" should be used for retrieval
        self.assertIn(
            "alex_123",
            retrieve_user_ids,
            f"'alex_123' should be used as user_id for memory "
            f"retrieval. Calls made: "
            f"{self.provider.retrieve_calls}",
        )

    def test_diagnostics_memory_types_include_shared(
        self,
    ) -> None:
        """The diagnostics should report memory_types from the
        shared memories (profile, task_context).
        """
        query = _make_llm_query(
            "What am I working on?"
        )

        _, diagnostics = self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id="alex_123",
        )

        memory_types = diagnostics["memory_types"]
        self.assertIn(
            "profile",
            memory_types,
            f"'profile' memory_type should be in diagnostics. "
            f"Got: {memory_types}",
        )
        self.assertIn(
            "task_context",
            memory_types,
            f"'task_context' memory_type should be in "
            f"diagnostics. Got: {memory_types}",
        )

    def test_no_user_id_falls_back_to_agent_name(
        self,
    ) -> None:
        """When no user_id is provided, inject() should fall
        back to agent_name for own-memory retrieval and NOT
        attempt shared retrieval.

        This documents the backward-compatible behavior.
        """
        query = _make_llm_query(
            "What programming language do I prefer?"
        )

        _, diagnostics = self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id=None,
        )

        # resolved_user_id should be None (no user_id to scope)
        self.assertIsNone(
            diagnostics["resolved_user_id"],
            "resolved_user_id should be None when no user_id "
            "is provided",
        )

        # Retrieval should use "assistant_agent" as fallback
        retrieve_user_ids = [
            call["user_id"]
            for call in self.provider.retrieve_calls
        ]
        self.assertIn(
            "assistant_agent",
            retrieve_user_ids,
            "Without explicit user_id, should fall back to "
            "'assistant_agent' for own-memory retrieval",
        )

    def test_shared_retrieval_excludes_requesting_agent(
        self,
    ) -> None:
        """The shared memory retrieval call should pass the
        requesting agent_name so the provider can exclude the
        agent's own memories from the shared result set.
        """
        query = _make_llm_query(
            "What am I working on?"
        )

        self.injector.inject(
            agent_name="assistant_agent",
            query=query,
            user_id="alex_123",
        )

        # Find the shared retrieval call (has sharing_policy)
        shared_calls = [
            call for call in self.provider.retrieve_calls
            if call.get("sharing_policy") == "shared"
        ]

        self.assertGreater(
            len(shared_calls), 0,
            "There should be at least one shared retrieval call",
        )

        # The shared call should include agent_name for
        # exclusion filtering
        for call in shared_calls:
            self.assertEqual(
                call["agent_name"],
                "assistant_agent",
                "Shared retrieval should pass agent_name for "
                "exclusion filtering",
            )


if __name__ == "__main__":
    unittest.main()
