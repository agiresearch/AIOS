"""
Regression Tests: Per-Request User Identity in Memory Context Injection

This module tests two distinct behaviors of the user_id resolution
system in ``ContextInjector._resolve_user_id()``:

1. **Legacy fallback** (no explicit ``user_id`` on the request):
   Uses ``MemoryManager.latest_user_id`` as a best-effort guess.
   This path is preserved for backward compatibility but is UNSAFE
   for multi-user scenarios (return-visit contamination).

2. **Request-scoped** (explicit ``user_id`` passed to ``inject()``):
   Uses the per-request identity directly, preventing cross-user
   memory contamination regardless of what ``latest_user_id`` says.

Run:
    pytest tests/modules/memory/test_user_id_caching_bug_repro.py -v
"""
from __future__ import annotations

import os
import sys
import time
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional

# Ensure project root on sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.access import AccessManager
from aios.memory.context_injector import ContextInjector
from aios.memory.providers.base import MemoryProvider
from aios.memory.write_barrier import MemoryWriteBarrier


# ------------------------------------------------------------------
# Synthetic users for multi-trial scenarios
# ------------------------------------------------------------------

SYNTHETIC_USERS = [
    {
        "user_id": "jordan_matthews_75157bae",
        "profile": "Jordan Matthews is a backend engineer who loves Go.",
        "memory_type": "profile",
    },
    {
        "user_id": "julia_romero_a3e82c1f",
        "profile": "Julia Romero is a data scientist who prefers R.",
        "memory_type": "profile",
    },
    {
        "user_id": "olivia_ramirez_d9f04b72",
        "profile": (
            "Olivia Ramirez is a DevOps engineer who uses Terraform."
        ),
        "memory_type": "profile",
    },
    {
        "user_id": "ethan_nakamura_1b5c7d9e",
        "profile": "Ethan Nakamura is a frontend dev who uses Svelte.",
        "memory_type": "profile",
    },
    {
        "user_id": "maya_patel_e8a3f620",
        "profile": (
            "Maya Patel is a security researcher who codes in Rust."
        ),
        "memory_type": "profile",
    },
]


# ------------------------------------------------------------------
# Test infrastructure
# ------------------------------------------------------------------


class TracingProvider(MemoryProvider):
    """Provider that records all operations and returns memories
    scoped by user_id, simulating correct ChromaDB WHERE filtering.
    """

    def __init__(self) -> None:
        self._store: Dict[str, List[dict]] = {}
        self.retrieve_log: List[Dict[str, Any]] = []
        self.add_log: List[Dict[str, Any]] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        metadata = getattr(memory_note, "metadata", {}) or {}
        user_id = metadata.get("user_id", "unknown")
        content = getattr(memory_note, "content", "")
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.95,
        }
        self._store.setdefault(user_id, []).append(mem)
        self.add_log.append({
            "user_id": user_id,
            "content": content,
            "metadata": dict(metadata),
            "timestamp": time.monotonic(),
        })
        return MemoryResponse(success=True, memory_id="mem-ok")

    def store_for_user(
        self, user_id: str, content: str, metadata: dict
    ) -> None:
        """Seed the store directly (bypasses add_memory logging)."""
        mem = {
            "content": content,
            "metadata": dict(metadata),
            "score": 0.95,
        }
        self._store.setdefault(user_id, []).append(mem)

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="mem-ok")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        user_id = query.params.get("user_id")
        agent_name = query.params.get("agent_name")
        self.retrieve_log.append({
            "user_id_in_query": user_id,
            "agent_name": agent_name,
            "params": dict(query.params),
            "timestamp": time.monotonic(),
        })
        results = []
        for item in self._store.get(user_id, []):
            results.append({
                "content": item["content"],
                "metadata": dict(item.get("metadata", {})),
                "score": item.get("score", 0.9),
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


class FakeMemoryManager:
    """Mirrors the real MemoryManager's user_id registry."""

    def __init__(self, provider: TracingProvider) -> None:
        self.provider = provider
        self.barrier = MemoryWriteBarrier(config={})
        # Profile and task agents admit the assistant agent to
        # their privilege groups.
        self.access_manager = AccessManager({
            "profile_agent": ["assistant_agent"],
            "task_agent": ["assistant_agent"],
        })
        self._known_user_ids: OrderedDict[str, float] = (
            OrderedDict()
        )

    @property
    def known_user_ids(self) -> set:
        return set(self._known_user_ids.keys())

    @property
    def latest_user_id(self) -> Optional[str]:
        if not self._known_user_ids:
            return None
        return next(reversed(self._known_user_ids))

    def _register_user_id(self, user_id: str) -> None:
        self._known_user_ids[user_id] = time.monotonic()
        self._known_user_ids.move_to_end(user_id)


# ==================================================================
# SECTION 1: No-Fallback Behavior (post-fix)
#
# These tests document how _resolve_user_id() behaves when NO
# explicit request_user_id is provided. After the fix, the
# injector returns None (not latest_user_id), causing the caller
# to fall back to agent_name for own-memory queries. No cross-user
# contamination is possible.
# ==================================================================


class TestLegacyFallbackBehavior(unittest.TestCase):
    """Tests for the no-fallback path where no explicit
    request_user_id is passed to inject().

    Post-fix, ``_resolve_user_id()`` returns ``None`` when no
    explicit ``request_user_id`` is provided, preventing
    cross-user memory contamination. The caller uses
    ``agent_name`` as the own-memory scope (safe default).
    """

    def setUp(self) -> None:
        self.provider = TracingProvider()
        self.manager = FakeMemoryManager(provider=self.provider)
        self.injector = ContextInjector(
            memory_manager=self.manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

    def _make_query(self, text: str = "Hello") -> LLMQuery:
        return LLMQuery(
            messages=[{"role": "user", "content": text}],
            action_type="chat",
        )

    def _get_system_content(self, query: LLMQuery) -> str:
        for msg in query.messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "MEMORY CONTEXT" in content:
                    return content
        return ""

    def test_legacy_fallback_uses_latest_user_id_when_request_user_id_missing(
        self,
    ) -> None:
        """Without explicit user_id, _resolve_user_id returns None
        (not latest_user_id). This prevents cross-user contamination.
        """
        self.manager._register_user_id("jordan_matthews_75157bae")
        self.manager._register_user_id("olivia_ramirez_d9f04b72")

        resolved = self.injector._resolve_user_id(
            "assistant_agent"
        )
        self.assertIsNone(resolved)

    def test_legacy_fallback_sequential_forward_works_by_coincidence(
        self,
    ) -> None:
        """Without explicit user_id, resolved_user_id is always
        None regardless of registration order.
        """
        results = []
        for i, user in enumerate(SYNTHETIC_USERS):
            uid = user["user_id"]
            self.provider.store_for_user(
                user_id=uid,
                content=user["profile"],
                metadata={
                    "user_id": uid,
                    "owner_agent": "profile_agent",
                    "sharing_policy": "shared",
                    "memory_type": "profile",
                },
            )
            self.manager._register_user_id(uid)
            query = self._make_query(f"Trial {i + 1}")
            _, diag = self.injector.inject(
                "assistant_agent", query
            )
            results.append(diag["resolved_user_id"])

        # Without explicit user_id, resolved is always None
        for result in results:
            self.assertIsNone(result)

    def test_legacy_fallback_return_visit_uses_latest_not_requesting_user(
        self,
    ) -> None:
        """Without explicit user_id, no user-scoped memories are
        injected. resolved_user_id is None and no contamination
        occurs.
        """
        users = SYNTHETIC_USERS[:3]
        for user in users:
            uid = user["user_id"]
            self.provider.store_for_user(
                user_id=uid,
                content=user["profile"],
                metadata={
                    "user_id": uid,
                    "owner_agent": "profile_agent",
                    "sharing_policy": "shared",
                    "memory_type": "profile",
                },
            )
            self.manager._register_user_id(uid)

        # Jordan returns but no explicit user_id is passed.
        # Post-fix: resolved_user_id is None, no contamination.
        query = self._make_query("What language do I prefer?")
        result_query, diag = self.injector.inject(
            "assistant_agent", query
        )

        # Expected: resolved_user_id is None (no fallback)
        self.assertIsNone(diag["resolved_user_id"])

    def test_legacy_fallback_all_retrieves_use_same_stale_user_id(
        self,
    ) -> None:
        """Without explicit user_id, all requests use agent_name
        as the own-memory scope (resolved_user_id=None).
        """
        users = SYNTHETIC_USERS[:3]
        for user in users:
            uid = user["user_id"]
            self.provider.store_for_user(
                user_id=uid,
                content=user["profile"],
                metadata={
                    "user_id": uid,
                    "owner_agent": "profile_agent",
                    "sharing_policy": "shared",
                    "memory_type": "profile",
                },
            )
            self.manager._register_user_id(uid)

        self.provider.retrieve_log.clear()
        for trial in range(3):
            query = self._make_query(f"Request {trial + 1}")
            self.injector.inject("assistant_agent", query)

        unique_ids = {
            e["user_id_in_query"]
            for e in self.provider.retrieve_log
        }
        # All use agent_name (no fallback to latest_user_id)
        self.assertEqual(len(unique_ids), 1)
        self.assertIn("assistant_agent", unique_ids)


# ==================================================================
# SECTION 2: Request-Scoped User Identity (the fix)
#
# These tests verify that when an explicit user_id is passed to
# inject(), it is used directly for memory retrieval, preventing
# cross-user contamination regardless of latest_user_id.
# ==================================================================


class TestRequestScopedUserIdentity(unittest.TestCase):
    """Regression tests for the per-request user_id fix.

    When ``inject(agent_name, query, user_id=X)`` is called with
    an explicit ``user_id``, retrieval MUST be scoped to X —
    regardless of what ``latest_user_id`` says.
    """

    def setUp(self) -> None:
        self.provider = TracingProvider()
        self.manager = FakeMemoryManager(provider=self.provider)
        self.injector = ContextInjector(
            memory_manager=self.manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

    def _make_query(self, text: str = "Hello") -> LLMQuery:
        return LLMQuery(
            messages=[{"role": "user", "content": text}],
            action_type="chat",
        )

    def _get_system_content(self, query: LLMQuery) -> str:
        for msg in query.messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "MEMORY CONTEXT" in content:
                    return content
        return ""

    def _seed_all_users(self) -> None:
        """Pre-populate provider with all synthetic users."""
        for user in SYNTHETIC_USERS:
            uid = user["user_id"]
            self.provider.store_for_user(
                user_id=uid,
                content=user["profile"],
                metadata={
                    "user_id": uid,
                    "owner_agent": "profile_agent",
                    "sharing_policy": "shared",
                    "memory_type": "profile",
                },
            )
            self.manager._register_user_id(uid)

    # ----------------------------------------------------------
    # Core fix tests
    # ----------------------------------------------------------

    def test_request_user_id_prevents_return_visit_contamination(
        self,
    ) -> None:
        """With explicit user_id, Jordan gets Jordan's memories
        even though Olivia was the last to write.
        """
        self._seed_all_users()

        # latest_user_id is maya (last registered)
        self.assertEqual(
            self.manager.latest_user_id,
            "maya_patel_e8a3f620",
        )

        # Jordan comes back with explicit identity
        query = self._make_query("What language do I prefer?")
        result_query, diag = self.injector.inject(
            "assistant_agent",
            query,
            user_id="jordan_matthews_75157bae",
        )

        self.assertEqual(
            diag["resolved_user_id"],
            "jordan_matthews_75157bae",
        )
        injected = self._get_system_content(result_query)
        self.assertIn("Go", injected)
        self.assertNotIn("Terraform", injected)
        self.assertNotIn("Rust", injected)

    def test_request_user_id_overrides_latest_user_id(
        self,
    ) -> None:
        """_resolve_user_id(agent, request_user_id=X) returns X
        even when latest_user_id is different.
        """
        self.manager._register_user_id("jordan_matthews_75157bae")
        self.manager._register_user_id("olivia_ramirez_d9f04b72")

        resolved = self.injector._resolve_user_id(
            "assistant_agent",
            request_user_id="jordan_matthews_75157bae",
        )
        self.assertEqual(resolved, "jordan_matthews_75157bae")

    def test_sequential_trials_with_explicit_user_id_are_isolated(
        self,
    ) -> None:
        """5 sequential trials with explicit user_id each get
        the correct user's memories, regardless of registration
        order.
        """
        self._seed_all_users()

        for user in SYNTHETIC_USERS:
            uid = user["user_id"]
            query = self._make_query(f"Tell me about myself")
            result_query, diag = self.injector.inject(
                "assistant_agent",
                query,
                user_id=uid,
            )
            self.assertEqual(
                diag["resolved_user_id"],
                uid,
                f"Trial for {uid}: wrong resolved_user_id",
            )
            injected = self._get_system_content(result_query)
            # Each user's profile mentions a unique technology
            unique_keyword = (
                user["profile"].split(" who ")[1].split(".")[0]
            )
            self.assertIn(
                unique_keyword,
                injected,
                f"Expected '{unique_keyword}' for {uid}",
            )

    def test_retrieve_log_shows_per_request_user_id(
        self,
    ) -> None:
        """When user_id is passed per-request, the provider
        retrieve_log shows distinct user_ids for each request.
        """
        self._seed_all_users()
        self.provider.retrieve_log.clear()

        users = SYNTHETIC_USERS[:3]
        for user in users:
            query = self._make_query(f"Request for {user['user_id']}")
            self.injector.inject(
                "assistant_agent",
                query,
                user_id=user["user_id"],
            )

        unique_ids = {
            e["user_id_in_query"]
            for e in self.provider.retrieve_log
        }
        self.assertEqual(
            len(unique_ids),
            3,
            f"Expected 3 distinct user_ids, got {unique_ids}",
        )
        for user in users:
            self.assertIn(user["user_id"], unique_ids)

    def test_request_user_id_none_falls_back_to_none(
        self,
    ) -> None:
        """When user_id=None is passed (or omitted),
        _resolve_user_id returns None (no fallback to
        latest_user_id).
        """
        self.manager._register_user_id("jordan_matthews_75157bae")
        self.manager._register_user_id("olivia_ramirez_d9f04b72")

        # Explicit None behaves same as omitting the param
        resolved = self.injector._resolve_user_id(
            "assistant_agent",
            request_user_id=None,
        )
        self.assertIsNone(resolved)

    def test_request_user_id_equal_to_agent_name_falls_back(
        self,
    ) -> None:
        """If request_user_id == agent_name, it's treated as
        'no real user' and returns None.
        """
        self.manager._register_user_id("olivia_ramirez_d9f04b72")

        resolved = self.injector._resolve_user_id(
            "assistant_agent",
            request_user_id="assistant_agent",
        )
        # Returns None because request_user_id == agent_name
        self.assertIsNone(resolved)

    def test_interleaved_requests_for_different_users(
        self,
    ) -> None:
        """Simulates concurrent-style interleaved requests where
        different users alternate without new writes between them.
        """
        self._seed_all_users()
        self.provider.retrieve_log.clear()

        # Interleave: jordan, olivia, jordan, olivia, jordan
        pattern = [
            "jordan_matthews_75157bae",
            "olivia_ramirez_d9f04b72",
            "jordan_matthews_75157bae",
            "olivia_ramirez_d9f04b72",
            "jordan_matthews_75157bae",
        ]

        for uid in pattern:
            query = self._make_query(f"Who am I? ({uid})")
            _, diag = self.injector.inject(
                "assistant_agent", query, user_id=uid
            )
            self.assertEqual(diag["resolved_user_id"], uid)

        # Verify that the own-memory retrieval for each request
        # used the correct user_id. The retrieve_log also contains
        # shared-memory retrievals, so filter to own-memory calls
        # (those where user_id matches the pattern entry).
        own_retrieve_ids = [
            e["user_id_in_query"]
            for e in self.provider.retrieve_log
            if e["user_id_in_query"] in pattern
        ]
        # Each request produces at least one own-memory retrieve
        # with the correct user_id. Verify the unique ordering.
        # Deduplicate consecutive duplicates to get the pattern.
        deduped = []
        for uid in own_retrieve_ids:
            if not deduped or deduped[-1] != uid:
                deduped.append(uid)
        self.assertEqual(deduped, pattern)

    def test_diagnostics_resolved_user_id_matches_request(
        self,
    ) -> None:
        """The injection diagnostics always report the
        request-scoped user_id, not the global latest.
        """
        self._seed_all_users()

        # latest is maya, but request is julia
        query = self._make_query("Preferences?")
        _, diag = self.injector.inject(
            "assistant_agent",
            query,
            user_id="julia_romero_a3e82c1f",
        )

        self.assertEqual(
            diag["resolved_user_id"],
            "julia_romero_a3e82c1f",
        )
        # NOT maya (the latest)
        self.assertNotEqual(
            diag["resolved_user_id"],
            self.manager.latest_user_id,
        )


if __name__ == "__main__":
    unittest.main()
