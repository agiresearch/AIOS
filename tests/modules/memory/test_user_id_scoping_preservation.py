"""
Preservation property tests for the mem0 user_id scoping bugfix.

These tests encode the CURRENT baseline behavior that MUST be preserved
after the fix is applied.  They MUST PASS on both the unfixed and fixed
code — failure on the unfixed code means the test is wrong (we are
encoding existing behavior, not expected behavior).

Properties tested:
  P-1: Fallback to agent_name when known_user_ids is empty
  P-4: ConversationExtractor stores under effective user_id
  P-5: _apply_sharing_filter() privacy invariant
  P-6: Disabled injection is always a no-op

Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5
"""
from __future__ import annotations

import os
import sys
import threading
import unittest
from typing import Any, Dict, List, Optional
from unittest.mock import patch

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from hypothesis import given, settings, strategies as st, assume
from hypothesis import HealthCheck

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
# Test double: RecordingProvider (reused from exploration test)
# ------------------------------------------------------------------


class RecordingProvider(MemoryProvider):
    """A minimal provider that records calls and returns
    configurable results."""

    def __init__(self) -> None:
        self.retrieve_calls: List[MemoryQuery] = []
        self.add_calls: List[Any] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        self.add_calls.append(memory_note)
        return MemoryResponse(success=True, memory_id="test-id")

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="test-id")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Record the call and return empty results."""
        self.retrieve_calls.append(query)
        return MemoryResponse(success=True, search_results=[])

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
    """Minimal mock MemoryManager with configurable known_user_ids."""

    def __init__(
        self,
        provider: MemoryProvider,
        known_user_ids: set | None = None,
    ) -> None:
        self.provider = provider
        self.known_user_ids = known_user_ids or set()
        self.barrier = MemoryWriteBarrier(config={})
        self.access_manager = AccessManager()


# ------------------------------------------------------------------
# Strategies
# ------------------------------------------------------------------

# Strategy for valid agent names (non-empty, no leading underscores)
agent_name_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="_",
    ),
    min_size=3,
    max_size=20,
).filter(
    lambda s: not s.startswith("_")
    and "__" not in s
    and len(s.strip()) > 0
)

# Strategy for user messages (non-empty text)
user_message_st = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "Z"),
    ),
    min_size=1,
    max_size=100,
).filter(lambda s: len(s.strip()) > 0)


# ------------------------------------------------------------------
# Property P-1: Fallback to agent_name with empty known_user_ids
# ------------------------------------------------------------------


class TestP1FallbackToAgentName(unittest.TestCase):
    """Property P-1: For all (agent_name, messages) with empty
    known_user_ids, inject() own-memory query uses
    user_id=agent_name.

    This ensures backward compatibility: when no real end-user
    identifiers are registered, the system scopes own-memory
    retrieval to agent_name (the legacy behavior).

    Validates: Requirement 3.1
    """

    @given(
        agent_name=agent_name_st,
        user_msg=user_message_st,
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
        ],
    )
    def test_p1_empty_known_user_ids_uses_agent_name(
        self,
        agent_name: str,
        user_msg: str,
    ) -> None:
        """**Validates: Requirements 3.1**

        When known_user_ids is empty, the own-memory query
        MUST use user_id=agent_name (backward compat).
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(
            provider=provider,
            known_user_ids=set(),  # empty!
        )

        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        llm_query = LLMQuery(
            messages=[
                {"role": "user", "content": user_msg},
            ],
            action_type="chat",
        )

        _, diagnostics = injector.inject(agent_name, llm_query)

        # At least one retrieve call must have been made.
        self.assertGreater(
            len(provider.retrieve_calls),
            0,
            "No retrieve_memory calls were made.",
        )

        # The first (own-memory) query must use agent_name
        # as user_id when no known_user_ids exist.
        own_query = provider.retrieve_calls[0]
        own_query_user_id = own_query.params.get("user_id")
        self.assertEqual(
            own_query_user_id,
            agent_name,
            (
                f"P-1 VIOLATION: With empty known_user_ids, "
                f"own-memory query used user_id='{own_query_user_id}' "
                f"but expected agent_name='{agent_name}'."
            ),
        )


# ------------------------------------------------------------------
# Property P-4: ConversationExtractor stores under effective user_id
# ------------------------------------------------------------------


class TestP4ConversationExtractorScoping(unittest.TestCase):
    """Property P-4: For all (agent_name, user_id) passed to
    ConversationExtractor.extract_async(), stored memory has
    metadata["user_id"] == user_id or agent_name.

    When user_id is provided, the extractor uses it.
    When user_id is None, the extractor falls back to agent_name.

    Validates: Requirement 3.1, 3.2
    """

    @given(
        agent_name=agent_name_st,
        user_id=st.one_of(
            st.none(),
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("L", "N"),
                    whitelist_characters="_",
                ),
                min_size=5,
                max_size=30,
            ).filter(lambda s: len(s.strip()) > 0),
        ),
        user_msg=user_message_st,
        assistant_msg=user_message_st,
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
        ],
    )
    def test_p4_extractor_stores_under_effective_user_id(
        self,
        agent_name: str,
        user_id: Optional[str],
        user_msg: str,
        assistant_msg: str,
    ) -> None:
        """**Validates: Requirements 3.1, 3.2**

        ConversationExtractor._store_conversation stores memory
        under effective_user_id = user_id or agent_name.
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(provider=provider)

        extractor = ConversationExtractor(
            memory_manager=manager,
            config={"auto_extract": True},
        )

        # Call the synchronous internal method directly to
        # avoid threading complexity in tests.
        extractor._store_conversation(
            agent_name=agent_name,
            user_message=user_msg,
            assistant_message=assistant_msg,
            user_id=user_id,
        )

        # Verify a memory was added.
        self.assertEqual(
            len(provider.add_calls),
            1,
            "Expected exactly one add_memory call.",
        )

        stored_note = provider.add_calls[0]
        stored_user_id = stored_note.metadata.get("user_id")
        expected_user_id = user_id or agent_name

        self.assertEqual(
            stored_user_id,
            expected_user_id,
            (
                f"P-4 VIOLATION: Stored memory user_id="
                f"'{stored_user_id}' but expected "
                f"'{expected_user_id}' (user_id={user_id!r}, "
                f"agent_name='{agent_name}')."
            ),
        )


# ------------------------------------------------------------------
# Property P-5: Privacy filter invariant
# ------------------------------------------------------------------


class TestP5PrivacyFilterInvariant(unittest.TestCase):
    """Property P-5: For all memories with sharing_policy="private"
    and owner_agent != agent_name, _apply_sharing_filter() excludes
    them.

    The privacy invariant MUST NOT change: foreign private memories
    are never returned regardless of other filter parameters.

    Validates: Requirement 3.3
    """

    @given(
        agent_name=agent_name_st,
        owner_agent=agent_name_st,
        user_id_filter=st.one_of(
            st.none(),
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("L", "N"),
                    whitelist_characters="_",
                ),
                min_size=3,
                max_size=20,
            ),
        ),
        sharing_policy_filter=st.one_of(
            st.none(),
            st.just("private"),
            st.just("shared"),
        ),
    )
    @settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
        ],
    )
    def test_p5_foreign_private_memories_excluded(
        self,
        agent_name: str,
        owner_agent: str,
        user_id_filter: Optional[str],
        sharing_policy_filter: Optional[str],
    ) -> None:
        """**Validates: Requirements 3.3**

        A memory with sharing_policy="private" and
        owner_agent != agent_name MUST be excluded from results.
        """
        # Precondition: the memory is owned by a DIFFERENT agent.
        assume(owner_agent != agent_name)

        candidates = [
            {
                "content": "Private memory from foreign agent",
                "metadata": {
                    "user_id": "some_user",
                    "owner_agent": owner_agent,
                    "sharing_policy": "private",
                    "memory_type": "conversation",
                },
                "score": 0.95,
            },
        ]

        result = _apply_sharing_filter(
            candidates=candidates,
            agent_name=agent_name,
            user_id=user_id_filter,
            sharing_policy=sharing_policy_filter,
            get_metadata=lambda item: item.get("metadata", {}),
        )

        self.assertEqual(
            len(result),
            0,
            (
                f"P-5 VIOLATION: Foreign private memory was "
                f"returned! agent_name='{agent_name}', "
                f"owner_agent='{owner_agent}', "
                f"user_id_filter={user_id_filter!r}, "
                f"sharing_policy_filter="
                f"{sharing_policy_filter!r}"
            ),
        )


# ------------------------------------------------------------------
# Property P-6: Disabled injection is a no-op
# ------------------------------------------------------------------


class TestP6DisabledInjectionNoOp(unittest.TestCase):
    """Property P-6: For all (agent_name, messages) with
    auto_inject=False, inject() returns the original query with
    injected_count=0 and auto_inject_enabled=False.

    Disabled injection must NEVER issue retrieval calls or
    modify the query.

    Validates: Requirement 3.5
    """

    @given(
        agent_name=agent_name_st,
        user_msg=user_message_st,
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
        ],
    )
    def test_p6_disabled_inject_is_noop(
        self,
        agent_name: str,
        user_msg: str,
    ) -> None:
        """**Validates: Requirements 3.5**

        When auto_inject=False, inject() must:
        - NOT issue any retrieval calls
        - Return injected_count=0
        - Return auto_inject_enabled=False
        - Not modify the query messages
        """
        provider = RecordingProvider()
        manager = MockMemoryManager(
            provider=provider,
            known_user_ids={"some_user__kernel_shared"},
        )

        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": False,  # DISABLED
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        original_messages = [
            {"role": "user", "content": user_msg},
        ]
        llm_query = LLMQuery(
            messages=list(original_messages),
            action_type="chat",
        )

        returned_query, diagnostics = injector.inject(
            agent_name, llm_query
        )

        # No retrieval calls should be made.
        self.assertEqual(
            len(provider.retrieve_calls),
            0,
            (
                f"P-6 VIOLATION: auto_inject=False but "
                f"{len(provider.retrieve_calls)} retrieve "
                f"calls were made."
            ),
        )

        # Diagnostics must show disabled state.
        self.assertFalse(
            diagnostics["auto_inject_enabled"],
            "P-6 VIOLATION: auto_inject_enabled should be False.",
        )
        self.assertEqual(
            diagnostics["injected_count"],
            0,
            "P-6 VIOLATION: injected_count should be 0.",
        )

        # Query messages should be unmodified.
        self.assertEqual(
            returned_query.messages,
            original_messages,
            "P-6 VIOLATION: Query messages were modified "
            "when auto_inject=False.",
        )


if __name__ == "__main__":
    unittest.main()
