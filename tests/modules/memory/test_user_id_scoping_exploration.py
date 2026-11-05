"""
Bug condition exploration tests for the mem0 user_id scoping bug.

These tests are EXPECTED TO FAIL on the unfixed code - their failure
confirms the bug exists.  They encode the EXPECTED (correct) behavior:
once the fix is applied, they will PASS.

Property BC-1: Own-memory isolation failure
    For all inject(agent_name, query) calls where known_user_ids is
    non-empty and contains entries different from agent_name:
      - The own-memory MemoryQuery.params["user_id"] MUST equal
        the most recently written user_id (latest_user_id)
      - The resolved_user_id MUST be that latest_user_id
      - Own-memory results MUST NOT contain memories from other users

On unfixed code:
  - params["user_id"] == agent_name (Bug 1.1)
  - The resolved user_id is picked from arbitrary set iteration (Bug 1.2)
  - user_id=agent_name filter returns ALL conversations (Bug 1.3)

Validates: Requirements 1.1, 1.2, 1.3
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
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
    results scoped by the user_id passed in the query.

    This simulates the real Mem0 behavior: when queried with
    user_id="agent_name", it returns ALL conversations (because
    that's how the buggy code stores them). When queried with a
    real user_id like "bob__kernel_shared", it returns only that
    user's memories.
    """

    def __init__(self, contaminated_agent_name: str) -> None:
        """
        Args:
            contaminated_agent_name: The agent_name that has
                contaminated memories stored under its name
                (simulating the pre-bug-fix state where
                conversations were stored under agent_name).
        """
        self._contaminated_agent_name = contaminated_agent_name
        # Record all retrieve_memory calls for inspection.
        self.retrieve_calls: List[MemoryQuery] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="test-id")

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(
            success=True, memory_id="test-id"
        )

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Record the call and return results based on user_id.

        When user_id == contaminated_agent_name, returns memories
        from MULTIPLE users (simulating the contamination bug).
        When user_id is a real user_id, returns only that user's
        memories.
        """
        self.retrieve_calls.append(query)
        user_id = query.params.get("user_id")
        agent_name = query.params.get("agent_name")
        sharing_policy = query.params.get("sharing_policy")

        if user_id == self._contaminated_agent_name:
            # BUG PATH: querying with agent_name returns
            # contaminated data from multiple users.
            results = [
                {
                    "content": "Memory from user Alice",
                    "metadata": {
                        "user_id": "alice__kernel_shared",
                        "owner_agent": (
                            self._contaminated_agent_name
                        ),
                        "sharing_policy": "private",
                        "memory_type": "conversation",
                    },
                    "score": 0.85,
                    "timestamp": "2025-01-01T00:00:00",
                    "keywords": [],
                    "tags": [],
                    "category": "Uncategorized",
                },
                {
                    "content": "Memory from user Bob",
                    "metadata": {
                        "user_id": "bob__kernel_shared",
                        "owner_agent": (
                            self._contaminated_agent_name
                        ),
                        "sharing_policy": "private",
                        "memory_type": "conversation",
                    },
                    "score": 0.80,
                    "timestamp": "2025-01-02T00:00:00",
                    "keywords": [],
                    "tags": [],
                    "category": "Uncategorized",
                },
            ]
        else:
            # CORRECT PATH: querying with a real user_id returns
            # only that user's memories.
            results = [
                {
                    "content": f"Memory for {user_id}",
                    "metadata": {
                        "user_id": user_id,
                        "owner_agent": (
                            self._contaminated_agent_name
                        ),
                        "sharing_policy": "private",
                        "memory_type": "conversation",
                    },
                    "score": 0.9,
                    "timestamp": "2025-01-03T00:00:00",
                    "keywords": [],
                    "tags": [],
                    "category": "Uncategorized",
                },
            ]

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
    """A minimal mock MemoryManager that exposes the known_user_ids
    set and barrier for ContextInjector to use.

    Uses an OrderedDict internally (matching the fixed MemoryManager)
    so that ``latest_user_id`` returns the most recently registered
    user_id deterministically.
    """

    def __init__(
        self,
        provider: MemoryProvider,
        known_user_ids: set,
        ordered_user_ids: "list[str] | None" = None,
    ) -> None:
        self.provider = provider
        self.barrier = MemoryWriteBarrier(config={})
        self.access_manager = AccessManager()
        # Build an OrderedDict from the ordered list (if given)
        # so that latest_user_id returns the last element.
        self._known_user_ids: OrderedDict = OrderedDict()
        if ordered_user_ids is not None:
            for uid in ordered_user_ids:
                self._known_user_ids[uid] = 0.0
        else:
            for uid in known_user_ids:
                self._known_user_ids[uid] = 0.0

    @property
    def known_user_ids(self) -> set:
        """Backward-compatible set view."""
        return set(self._known_user_ids.keys())

    @property
    def latest_user_id(self) -> "str | None":
        """Return the most recently written user_id, or None."""
        if not self._known_user_ids:
            return None
        return next(reversed(self._known_user_ids))


# ------------------------------------------------------------------
# Property-based exploration test
# ------------------------------------------------------------------


class UserIdScopingExplorationTests(unittest.TestCase):
    """Property BC-1: Own-memory isolation failure.

    Validates: Requirements 1.1, 1.2, 1.3
    """

    @given(
        agent_name=st.text(
            alphabet=st.characters(
                whitelist_categories=("L", "N"),
                whitelist_characters="_",
            ),
            min_size=3,
            max_size=20,
        ).filter(
            lambda s: not s.startswith("_")
            and "__" not in s
        ),
        user_ids=st.lists(
            st.text(
                alphabet=st.characters(
                    whitelist_categories=("L", "N"),
                    whitelist_characters="_",
                ),
                min_size=5,
                max_size=30,
            ).filter(
                lambda s: "__kernel_shared" in s
                or len(s) > 8
            ),
            min_size=1,
            max_size=3,
            unique=True,
        ),
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
            HealthCheck.filter_too_much,
        ],
    )
    def test_bc1_own_memory_query_uses_latest_user_id(
        self,
        agent_name: str,
        user_ids: List[str],
    ) -> None:
        """Property BC-1: For all (agent_name, user_ids) where
        |user_ids| > 0 and all(uid != agent_name for uid in
        user_ids):

            own_memory_query.params["user_id"] == latest_user_id
            AND resolved_user_id == latest_user_id

        On unfixed code:
        - params["user_id"] == agent_name (Bug 1.1 — FAILS)
        - resolved_user_id is arbitrary or None (Bug 1.2 — FAILS)
        """
        # Precondition: none of the user_ids should equal agent_name.
        assume(all(uid != agent_name for uid in user_ids))
        # Precondition: agent_name should not be empty.
        assume(len(agent_name.strip()) > 0)

        # The "latest" user_id is the last one in the list
        # (simulating most-recently-written).
        latest_user_id = user_ids[-1]

        # Build the known_user_ids as a plain set (current behavior).
        known_set = set(user_ids)

        # Create provider and manager.
        provider = RecordingProvider(
            contaminated_agent_name=agent_name
        )
        manager = MockMemoryManager(
            provider=provider,
            known_user_ids=known_set,
            ordered_user_ids=user_ids,
        )

        # Configure the injector with auto_inject=True.
        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        # Build a simple query.
        llm_query = LLMQuery(
            messages=[
                {"role": "user", "content": "Hello there!"},
            ],
            action_type="chat",
        )

        # Run injection with explicit user_id (as the production
        # path via _request_user_id would provide).
        _, diagnostics = injector.inject(
            agent_name, llm_query, user_id=latest_user_id,
        )

        # --- Assertion 1 (Bug 1.1): own-memory query user_id ---
        # The FIRST retrieve_memory call is the own-memory query.
        self.assertGreater(
            len(provider.retrieve_calls),
            0,
            "No retrieve_memory calls were made.",
        )

        own_query = provider.retrieve_calls[0]
        own_query_user_id = own_query.params.get("user_id")

        # EXPECTED: user_id != agent_name (should be a real user_id).
        # On UNFIXED code: user_id == agent_name → FAILS.
        self.assertNotEqual(
            own_query_user_id,
            agent_name,
            (
                f"BUG 1.1: own-memory query used "
                f"user_id='{own_query_user_id}' which equals "
                f"agent_name='{agent_name}'. Expected a real "
                f"end-user user_id from known_user_ids."
            ),
        )

        # --- Assertion 2 (Bug 1.2): resolved_user_id is latest ---
        # EXPECTED: own_query_user_id == latest_user_id.
        # On UNFIXED code: arbitrary set element → FAILS.
        self.assertEqual(
            own_query_user_id,
            latest_user_id,
            (
                f"BUG 1.2: own-memory query used "
                f"user_id='{own_query_user_id}' but expected "
                f"latest_user_id='{latest_user_id}'. The system "
                f"picked an arbitrary element from the set instead "
                f"of the most recently written user_id."
            ),
        )

        # --- Assertion 3 (Bug 1.3): results isolation ---
        # If the own-memory query correctly uses the real user_id,
        # results should NOT contain memories from other users.
        # On UNFIXED code, user_id=agent_name returns contaminated
        # data from multiple users.
        if own_query_user_id == agent_name:
            # If we got here (unfixed code), verify the contamination
            # manifests: results contain memories from multiple users.
            own_results_response = provider.retrieve_memory(
                own_query
            )
            if (
                own_results_response.success
                and own_results_response.search_results
            ):
                user_ids_in_results = set()
                for mem in own_results_response.search_results:
                    meta = mem.get("metadata", {})
                    uid = meta.get("user_id", "")
                    if uid:
                        user_ids_in_results.add(uid)
                # On unfixed code with agent_name filter, we get
                # memories from multiple users → contamination.
                self.assertLessEqual(
                    len(user_ids_in_results),
                    1,
                    (
                        f"BUG 1.3: own-memory query with "
                        f"user_id='{agent_name}' returned memories "
                        f"from multiple users: {user_ids_in_results}. "
                        f"Expected isolation to a single end-user."
                    ),
                )


if __name__ == "__main__":
    unittest.main()
