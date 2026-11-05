"""
Integration tests for multi-user isolation in the mem0 user_id
scoping fix.

These tests verify the full injection pipeline correctly isolates
memories per end-user across sequential trials, and that the
ConversationExtractor stores under the correct user_id.

Validates: Requirements 2.1, 2.2, 2.3, 3.1
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.access import AccessManager
from aios.memory.context_injector import ContextInjector
from aios.memory.conversation_extractor import ConversationExtractor
from aios.memory.providers.base import (
    MemoryProvider,
    _apply_sharing_filter,
    _enrich_metadata,
)
from aios.memory.write_barrier import MemoryWriteBarrier


# ------------------------------------------------------------------
# Test double: RecordingProvider
# ------------------------------------------------------------------


class RecordingProvider(MemoryProvider):
    """A provider that records retrieve_memory calls and returns
    results scoped by user_id.

    Memories are stored per user_id in a dict.  When queried, only
    memories matching the requested user_id are returned, simulating
    the correct ChromaDB WHERE filter behavior.
    """

    def __init__(self) -> None:
        # user_id -> list of memory dicts
        self._store: Dict[str, List[dict]] = {}
        # Record all retrieve_memory calls for inspection.
        self.retrieve_calls: List[MemoryQuery] = []
        # Record all add_memory calls for inspection.
        self.add_calls: List[Any] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        """Store a memory under the user_id in its metadata."""
        self.add_calls.append(memory_note)
        metadata = getattr(memory_note, "metadata", {}) or {}
        user_id = metadata.get("user_id", "unknown")
        content = getattr(memory_note, "content", "")
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.9,
            "timestamp": "2025-01-01T00:00:00",
            "keywords": [],
            "tags": [],
            "category": "Uncategorized",
        }
        self._store.setdefault(user_id, []).append(mem)
        return MemoryResponse(success=True, memory_id="test-id")

    def store_memory(
        self, user_id: str, content: str, metadata: dict
    ) -> None:
        """Convenience method to pre-populate the store."""
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.9,
            "timestamp": "2025-01-01T00:00:00",
            "keywords": [],
            "tags": [],
            "category": "Uncategorized",
        }
        self._store.setdefault(user_id, []).append(mem)

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="test-id")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Return memories matching the requested user_id."""
        self.retrieve_calls.append(query)
        user_id = query.params.get("user_id")
        agent_name = query.params.get("agent_name")
        sharing_policy = query.params.get("sharing_policy")

        # Return only memories stored under the requested user_id.
        results = list(self._store.get(user_id, []))

        # Apply sharing filter like the real provider does.
        if agent_name is not None:
            results = _apply_sharing_filter(
                results,
                agent_name,
                user_id,
                sharing_policy,
                lambda item: item.get("metadata", {}),
            )

        # Enrich metadata on results.
        search_results = []
        for item in results:
            metadata = _enrich_metadata(
                dict(item.get("metadata", {}))
            )
            search_results.append({
                "content": item.get("content", ""),
                "keywords": metadata.get("keywords", []),
                "tags": metadata.get("tags", []),
                "category": metadata.get(
                    "category", "Uncategorized"
                ),
                "timestamp": metadata.get("timestamp", ""),
                "score": item.get("score"),
                "metadata": metadata,
            })

        return MemoryResponse(
            success=True, search_results=search_results
        )

    def retrieve_memory_raw(
        self, query: MemoryQuery
    ) -> List[Any]:
        return []

    def close(self) -> None:
        pass


# ------------------------------------------------------------------
# Mock MemoryManager
# ------------------------------------------------------------------


class MockMemoryManager:
    """A minimal mock MemoryManager with the real OrderedDict-based
    _known_user_ids, _register_user_id() method, and
    latest_user_id property.
    """

    def __init__(self, provider: MemoryProvider) -> None:
        self.provider = provider
        self.barrier = MemoryWriteBarrier(config={})
        self.access_manager = AccessManager()
        self._known_user_ids: OrderedDict[str, float] = (
            OrderedDict()
        )

    @property
    def known_user_ids(self) -> set:
        """Backward-compatible set view."""
        return set(self._known_user_ids.keys())

    @property
    def latest_user_id(self) -> Optional[str]:
        """Return the most recently written user_id, or None."""
        if not self._known_user_ids:
            return None
        return next(reversed(self._known_user_ids))

    def _register_user_id(self, user_id: str) -> None:
        """Register a user_id with current timestamp, moving
        to end of the ordered registry."""
        import time

        self._known_user_ids[user_id] = time.monotonic()
        self._known_user_ids.move_to_end(user_id)


# ------------------------------------------------------------------
# Integration Tests
# ------------------------------------------------------------------


class TestMultiUserIsolation(unittest.TestCase):
    """Integration tests verifying end-to-end multi-user isolation
    in the injection pipeline.

    Validates: Requirements 2.1, 2.2, 2.3, 3.1
    """

    def _make_injector(
        self, manager: MockMemoryManager
    ) -> ContextInjector:
        """Create a ContextInjector with auto_inject enabled."""
        return ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

    def _make_query(self, text: str = "Hello!") -> LLMQuery:
        """Create a simple chat LLMQuery."""
        return LLMQuery(
            messages=[{"role": "user", "content": text}],
            action_type="chat",
        )

    # ----------------------------------------------------------
    # Test 1: Multi-user sequential trials
    # ----------------------------------------------------------

    def test_multi_user_sequential_trials(self) -> None:
        """Trial 1: sophia's memories are retrieved for sophia.
        Trial 2: after registering alex, only alex's memories
        are retrieved — NOT sophia's.

        Validates: Requirements 2.1, 2.3
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(provider=provider)
        injector = self._make_injector(manager)

        # --- Pre-populate provider with per-user memories ---
        provider.store_memory(
            user_id="sophia__kernel_shared",
            content="Sophia likes Python",
            metadata={
                "user_id": "sophia__kernel_shared",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )
        provider.store_memory(
            user_id="alex__kernel_shared",
            content="Alex likes Rust",
            metadata={
                "user_id": "alex__kernel_shared",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )

        # --- Trial 1: Register sophia, inject for sophia ---
        manager._register_user_id("sophia__kernel_shared")

        query1 = self._make_query("What do I like?")
        result_query1, diag1 = injector.inject(
            "assistant_agent", query1,
            user_id="sophia__kernel_shared",
        )

        # Verify own-memory query used sophia's user_id.
        self.assertGreater(len(provider.retrieve_calls), 0)
        own_call_1 = provider.retrieve_calls[0]
        self.assertEqual(
            own_call_1.params["user_id"],
            "sophia__kernel_shared",
        )

        # Verify diagnostics resolved sophia.
        self.assertEqual(
            diag1["resolved_user_id"],
            "sophia__kernel_shared",
        )

        # Verify injected content is sophia's memory.
        injected_content = self._get_injected_content(
            result_query1
        )
        self.assertIn("Sophia likes Python", injected_content)
        self.assertNotIn("Alex likes Rust", injected_content)

        # --- Trial 2: Register alex, inject for alex ---
        provider.retrieve_calls.clear()
        manager._register_user_id("alex__kernel_shared")

        # Verify latest_user_id is now alex.
        self.assertEqual(
            manager.latest_user_id,
            "alex__kernel_shared",
        )

        query2 = self._make_query("What do I like?")
        result_query2, diag2 = injector.inject(
            "assistant_agent", query2,
            user_id="alex__kernel_shared",
        )

        # Verify own-memory query used alex's user_id.
        self.assertGreater(len(provider.retrieve_calls), 0)
        own_call_2 = provider.retrieve_calls[0]
        self.assertEqual(
            own_call_2.params["user_id"],
            "alex__kernel_shared",
        )

        # Verify diagnostics resolved alex.
        self.assertEqual(
            diag2["resolved_user_id"],
            "alex__kernel_shared",
        )

        # Verify injected content is alex's memory only.
        injected_content_2 = self._get_injected_content(
            result_query2
        )
        self.assertIn("Alex likes Rust", injected_content_2)
        self.assertNotIn(
            "Sophia likes Python", injected_content_2
        )

    # ----------------------------------------------------------
    # Test 2: Conversation stored under correct user_id
    # ----------------------------------------------------------

    def test_conversation_stored_under_correct_user_id(
        self,
    ) -> None:
        """After injection resolves user_id="alex__kernel_shared",
        verify extract_async() would store with that user_id and
        diagnostics contain the correct resolved_user_id.

        Validates: Requirements 2.2
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(provider=provider)
        injector = self._make_injector(manager)

        # Pre-populate alex's memory.
        provider.store_memory(
            user_id="alex__kernel_shared",
            content="Alex prefers dark mode",
            metadata={
                "user_id": "alex__kernel_shared",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )

        # Register alex.
        manager._register_user_id("alex__kernel_shared")

        # Run injection.
        query = self._make_query("Tell me about my preferences")
        _, diag = injector.inject(
            "assistant_agent", query,
            user_id="alex__kernel_shared",
        )

        # Verify resolved_user_id in diagnostics.
        self.assertEqual(
            diag["resolved_user_id"],
            "alex__kernel_shared",
        )

        # Now verify the ConversationExtractor stores under
        # the correct user_id by calling _store_conversation
        # directly (synchronous, avoids threading).
        extractor = ConversationExtractor(
            memory_manager=manager,
            config={"auto_extract": True},
        )
        extractor._store_conversation(
            agent_name="assistant_agent",
            user_message="Tell me about my preferences",
            assistant_message="You prefer dark mode.",
            user_id=diag["resolved_user_id"],
        )

        # The add_memory call should have stored with
        # metadata["user_id"] == "alex__kernel_shared".
        self.assertGreater(len(provider.add_calls), 0)
        stored_note = provider.add_calls[-1]
        stored_metadata = getattr(stored_note, "metadata", {})
        self.assertEqual(
            stored_metadata.get("user_id"),
            "alex__kernel_shared",
        )
        # Verify it is NOT stored under agent_name.
        self.assertNotEqual(
            stored_metadata.get("user_id"),
            "assistant_agent",
        )

    # ----------------------------------------------------------
    # Test 3: Backward compatibility with empty registry
    # ----------------------------------------------------------

    def test_backward_compatibility_empty_registry(
        self,
    ) -> None:
        """With empty _known_user_ids, own-memory query uses
        user_id=agent_name and diagnostics show
        resolved_user_id=None.

        Validates: Requirement 3.1 (P-1 integration check)
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(provider=provider)
        injector = self._make_injector(manager)

        # Pre-populate memories under agent_name (legacy
        # behavior scenario).
        provider.store_memory(
            user_id="assistant_agent",
            content="Legacy memory stored under agent_name",
            metadata={
                "user_id": "assistant_agent",
                "owner_agent": "assistant_agent",
                "sharing_policy": "private",
                "memory_type": "conversation",
            },
        )

        # Do NOT register any user_ids — registry is empty.
        self.assertEqual(len(manager._known_user_ids), 0)
        self.assertIsNone(manager.latest_user_id)

        # Run injection.
        query = self._make_query("What do you remember?")
        result_query, diag = injector.inject(
            "assistant_agent", query
        )

        # Verify own-memory query uses agent_name as fallback.
        self.assertGreater(len(provider.retrieve_calls), 0)
        own_call = provider.retrieve_calls[0]
        self.assertEqual(
            own_call.params["user_id"],
            "assistant_agent",
        )

        # Verify diagnostics show resolved_user_id=None.
        self.assertIsNone(diag["resolved_user_id"])

        # Verify the legacy memory was still retrieved.
        injected_content = self._get_injected_content(
            result_query
        )
        self.assertIn(
            "Legacy memory stored under agent_name",
            injected_content,
        )

    # ----------------------------------------------------------
    # Test 4: latest_user_id ordering
    # ----------------------------------------------------------

    def test_latest_user_id_ordering(self) -> None:
        """Register A, B, C in sequence → latest_user_id == C.
        Re-register A → latest_user_id == A (moved to end).

        Validates: Requirement 2.1
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(provider=provider)

        # Register A, B, C in sequence.
        manager._register_user_id("user_A")
        self.assertEqual(manager.latest_user_id, "user_A")

        manager._register_user_id("user_B")
        self.assertEqual(manager.latest_user_id, "user_B")

        manager._register_user_id("user_C")
        self.assertEqual(manager.latest_user_id, "user_C")

        # All three should be in known_user_ids.
        self.assertEqual(
            manager.known_user_ids,
            {"user_A", "user_B", "user_C"},
        )

        # Re-register A → should move to end.
        manager._register_user_id("user_A")
        self.assertEqual(manager.latest_user_id, "user_A")

        # Still three entries (no duplicates).
        self.assertEqual(
            manager.known_user_ids,
            {"user_A", "user_B", "user_C"},
        )

        # Verify internal order: B, C, A
        keys = list(manager._known_user_ids.keys())
        self.assertEqual(
            keys, ["user_B", "user_C", "user_A"]
        )

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------

    def _get_injected_content(self, query: LLMQuery) -> str:
        """Extract the injected memory system message content
        from the query, or return empty string if not present."""
        for msg in query.messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "MEMORY CONTEXT" in content:
                    return content
        return ""


if __name__ == "__main__":
    unittest.main()
