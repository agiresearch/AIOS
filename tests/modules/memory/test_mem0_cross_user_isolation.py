"""
Cross-user isolation regression test for the Mem0 retrieval pipeline.

PURPOSE:
Verifies that the AIOS kernel's memory retrieval — from ContextInjector
through Mem0Provider down to the Mem0 client.get_all() call — enforces
hard user_id partitioning at every layer.  No memory belonging to
user B should ever enter user A's candidate set, regardless of
sharing_policy or semantic similarity.

ARCHITECTURE UNDER TEST:
    ContextInjector.inject(agent_name, query, user_id="alice")
        → Mem0Provider.retrieve_memory(MemoryQuery(user_id="alice"))
            → _get_client_for_user("alice")
            → client.get_all(filters={"user_id": "alice"})
        → ContextInjector post-filter (owner_agent / sharing_policy)
        → Final injection into LLM query

ISOLATION INVARIANT:
    A memory whose metadata["user_id"] != resolved_user_id must NEVER
    appear in the injected context, even if:
    - It has sharing_policy="shared"
    - It is semantically identical to the query
    - It belongs to the same owner_agent

BUG EXPOSED:
    The ContextInjector's post-filter (enforce sharing_policy) checks
    only `owner_agent == agent_name OR sharing_policy == "shared"`.
    It does NOT verify `metadata["user_id"] == resolved_user_id`.
    If the upstream Mem0 filter is ever bypassed or weakened, memories
    from user B with sharing_policy="shared" would leak into user A's
    injection context.

    This test models that scenario by using a mock provider that
    returns BOTH users' memories (simulating broken or absent Mem0
    user_id filtering), then asserts the ContextInjector blocks
    cross-user results.  It FAILS against the current implementation
    because the injector trusts the provider's pre-filter entirely.

ADDITIONALLY:
    Mock-level contract tests verify that Mem0Provider.retrieve_memory()
    and retrieve_memory_raw() pass the resolved user_id inside the
    `filters` dict to client.get_all(), and NEVER as a top-level kwarg.

Run:
    pytest tests/modules/memory/test_mem0_cross_user_isolation.py -v
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

# Ensure project root on sys.path.
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
from aios.memory.providers.mem0 import Mem0Provider
from aios.memory.write_barrier import MemoryWriteBarrier


# ------------------------------------------------------------------
# Constants: two users with semantically similar memories
# ------------------------------------------------------------------

ALICE_USER_ID = "alice_wu_8e4f21ab"
BOB_USER_ID = "bob_chen_3c7d90ef"

# Both memories answer "What programming language do you prefer?"
ALICE_MEMORY_CONTENT = (
    "My preferred programming language is Python."
)
BOB_MEMORY_CONTENT = (
    "My preferred programming language is Rust."
)

TEST_AGENT = "assistant_agent"
PROFILE_AGENT = "profile_agent"
QUERY_TEXT = "What programming language do you prefer?"


# ------------------------------------------------------------------
# Section 1: Mock-level API contract tests for Mem0Provider
#
# These verify that client.get_all() receives the correct filters
# dict shape and that user_id is NEVER a top-level kwarg.
# ------------------------------------------------------------------


def _create_provider_with_mock() -> "tuple[Mem0Provider, MagicMock]":
    """Create a Mem0Provider with a mocked per-user client.

    The mock client's get_all() is a MagicMock so callers can
    inspect call_args.  The _get_client_for_user method is
    monkeypatched to always return this single mock (bypassing
    per-user collection routing for contract verification).
    """
    provider = Mem0Provider()
    mock_client = MagicMock()
    mock_client.get_all.return_value = []
    provider.client = mock_client
    provider.default_user_id = "default"
    provider.default_agent_id = None
    # Bypass per-user collection routing.
    provider._get_client_for_user = lambda uid: mock_client
    return provider, mock_client


class TestMem0FilterContract(unittest.TestCase):
    """Verify Mem0Provider passes user_id INSIDE filters dict,
    never as a top-level kwarg to client.get_all()."""

    # ---- retrieve_memory ----

    def test_retrieve_memory_passes_user_id_in_filters(self):
        """retrieve_memory must pass user_id inside filters dict."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        mock_client.get_all.assert_called_once()
        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertIn(
            "user_id", filters,
            "user_id must be present in the filters dict "
            "passed to client.get_all()",
        )
        self.assertEqual(
            filters["user_id"], ALICE_USER_ID,
            f"filters['user_id'] must be the resolved user_id "
            f"'{ALICE_USER_ID}', got '{filters.get('user_id')}'",
        )

    def test_retrieve_memory_no_top_level_user_id(self):
        """user_id must NOT be passed as a top-level kwarg to
        client.get_all() (deprecated Mem0 API)."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        _, kwargs = mock_client.get_all.call_args

        self.assertNotIn(
            "user_id", kwargs,
            "user_id must NOT be a top-level kwarg to get_all(). "
            "It belongs inside the 'filters' dict only.",
        )

    # ---- retrieve_memory_raw ----

    def test_retrieve_memory_raw_passes_user_id_in_filters(self):
        """retrieve_memory_raw must pass user_id inside filters."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory_raw",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory_raw(query)

        mock_client.get_all.assert_called_once()
        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertIn("user_id", filters)
        self.assertEqual(filters["user_id"], ALICE_USER_ID)

    def test_retrieve_memory_raw_no_top_level_user_id(self):
        """user_id must NOT be a top-level kwarg for raw retrieval."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory_raw",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory_raw(query)

        _, kwargs = mock_client.get_all.call_args

        self.assertNotIn(
            "user_id", kwargs,
            "user_id must NOT be a top-level kwarg for "
            "retrieve_memory_raw's get_all() call.",
        )

    # ---- Resolved identity correctness ----

    def test_filter_uses_resolved_user_id_not_agent_name(self):
        """When user_id is provided, the filter must use it
        verbatim — not the agent_name."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertNotEqual(
            filters["user_id"], TEST_AGENT,
            "The filter must use the resolved user_id, "
            "NOT the agent_name.",
        )

    def test_shared_retrieval_filter_uses_user_id(self):
        """When sharing_policy='shared' is requested (cross-agent
        path), the filter must still scope to the user_id."""
        provider, mock_client = _create_provider_with_mock()

        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 20,
                "user_id": ALICE_USER_ID,
                "sharing_policy": "shared",
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertEqual(
            filters["user_id"], ALICE_USER_ID,
            "Cross-agent shared retrieval must still pass "
            "user_id in the filters dict.",
        )


# ------------------------------------------------------------------
# Section 2: Cross-user isolation regression test via ContextInjector
#
# This is the critical test that FAILS against the current
# implementation.  It proves that the ContextInjector's post-filter
# does not independently enforce user_id isolation.
# ------------------------------------------------------------------


class LeakyMemoryProvider(MemoryProvider):
    """A mock provider that simulates broken user_id pre-filtering.

    When retrieve_memory is called, it returns memories from ALL
    users (as if the Mem0 get_all filter were bypassed or the
    per-user collection routing failed).  This exposes whether the
    ContextInjector's post-filter alone is sufficient to prevent
    cross-user memory leakage.
    """

    def __init__(self) -> None:
        self._all_memories: List[dict] = []
        self.retrieve_calls: List[dict] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def seed(self, content: str, metadata: dict) -> None:
        """Seed a memory directly."""
        self._all_memories.append({
            "content": content,
            "metadata": dict(metadata),
            "score": 0.95,
            "keywords": [],
            "tags": [],
            "category": "Uncategorized",
            "timestamp": "",
        })

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="ok")

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="ok")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not impl")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        """Return ALL memories regardless of user_id.

        This simulates a broken pre-filter: the provider does NOT
        enforce user_id scoping, returning memories for all users.
        The ContextInjector's post-filter is the only remaining
        defense.
        """
        params = query.params or {}
        self.retrieve_calls.append(dict(params))

        # INTENTIONALLY return all memories (broken filter)
        return MemoryResponse(
            success=True,
            search_results=list(self._all_memories),
        )

    def retrieve_memory_raw(
        self, query: MemoryQuery
    ) -> List[Any]:
        return []

    def close(self) -> None:
        pass

    def sync_llm_from_query(self, llms) -> None:
        pass


def _build_context_injector(
    provider: MemoryProvider,
) -> ContextInjector:
    """Build a ContextInjector with the given provider."""
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

    config = {
        "auto_inject": True,
        "max_injected_memories": 10,
        "relevance_threshold": 0.0,
        "max_memory_tokens": 3000,
    }

    return ContextInjector(
        memory_manager=manager, config=config
    )


def _make_llm_query(user_message: str) -> LLMQuery:
    """Build a minimal LLMQuery with a user message."""
    return LLMQuery(
        messages=[{"role": "user", "content": user_message}],
        tools=None,
        action_type="chat",
        message_return_type="text",
    )


class TestContextInjectorCrossUserIsolation(unittest.TestCase):
    """REGRESSION TEST: The ContextInjector must not inject memories
    belonging to a different user_id, even when the upstream provider
    fails to pre-filter correctly.

    This test FAILS against the current implementation because the
    ContextInjector's post-filter checks only:
        owner_agent == agent_name OR sharing_policy == "shared"
    It does NOT check:
        metadata["user_id"] == resolved_user_id

    Therefore, Bob's shared memory (sharing_policy="shared") passes
    the post-filter and leaks into Alice's injection context.
    """

    def setUp(self) -> None:
        self.provider = LeakyMemoryProvider()

        # Alice's memory: shared profile from profile_agent
        self.provider.seed(
            content=ALICE_MEMORY_CONTENT,
            metadata={
                "user_id": ALICE_USER_ID,
                "owner_agent": PROFILE_AGENT,
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        # Bob's memory: shared profile from profile_agent
        # Semantically similar to Alice's but for a DIFFERENT user.
        self.provider.seed(
            content=BOB_MEMORY_CONTENT,
            metadata={
                "user_id": BOB_USER_ID,
                "owner_agent": PROFILE_AGENT,
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        self.injector = _build_context_injector(self.provider)

    def test_alice_injection_excludes_bob_memory(self):
        """When injecting for Alice, Bob's memory must NOT appear
        in the injected context — even though Bob's memory has
        sharing_policy='shared' and is semantically relevant.

        The isolation invariant is:
            metadata["user_id"] != resolved_user_id → EXCLUDED

        This test FAILS if the ContextInjector does not enforce
        user_id at the post-filter level, relying solely on the
        provider's pre-filter (which is intentionally broken here).
        """
        query = _make_llm_query(QUERY_TEXT)

        result_query, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id=ALICE_USER_ID,
        )

        # Verify that injection happened
        injected_count = diagnostics.get("injected_count", 0)
        self.assertGreater(
            injected_count, 0,
            "At least one memory should be injected "
            "(Alice's shared profile memory).",
        )

        # Extract the injected content from the system message
        self.assertGreater(
            len(result_query.messages), 1,
            "A system message should be prepended with memories.",
        )
        injected_content = result_query.messages[0]["content"]

        # CRITICAL ASSERTION: Bob's memory must NOT be present
        self.assertNotIn(
            "Rust",
            injected_content,
            f"CROSS-USER LEAKAGE: Bob's memory about Rust "
            f"was injected into Alice's context. The "
            f"ContextInjector's post-filter does not check "
            f"metadata['user_id'] == resolved_user_id. "
            f"Injected content: {injected_content!r}",
        )

        # Alice's memory SHOULD be present
        self.assertIn(
            "Python",
            injected_content,
            "Alice's own shared memory about Python should "
            "be injected.",
        )

    def test_bob_injection_excludes_alice_memory(self):
        """Symmetric test: when injecting for Bob, Alice's memory
        must not appear."""
        query = _make_llm_query(QUERY_TEXT)

        result_query, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id=BOB_USER_ID,
        )

        injected_count = diagnostics.get("injected_count", 0)
        self.assertGreater(injected_count, 0)

        injected_content = result_query.messages[0]["content"]

        self.assertNotIn(
            "Python",
            injected_content,
            f"CROSS-USER LEAKAGE: Alice's memory about Python "
            f"was injected into Bob's context. "
            f"Injected content: {injected_content!r}",
        )

        self.assertIn(
            "Rust",
            injected_content,
            "Bob's own shared memory about Rust should "
            "be injected.",
        )

    def test_injected_count_excludes_wrong_user(self):
        """injected_count must reflect only the correct user's
        memories, not all semantically relevant memories."""
        query = _make_llm_query(QUERY_TEXT)

        _, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id=ALICE_USER_ID,
        )

        # Only Alice's memory should be counted
        self.assertEqual(
            diagnostics["injected_count"], 1,
            f"Only 1 memory (Alice's) should be injected. "
            f"Got {diagnostics['injected_count']}. "
            f"If 2, Bob's memory leaked through.",
        )

    def test_candidate_set_should_not_include_wrong_user(self):
        """The candidate_count before relevance filtering should
        also exclude wrong-user memories.  This verifies that
        user_id isolation happens BEFORE scoring, not after.

        Note: In the current implementation with a properly-
        filtering provider, candidates are already user-scoped.
        With a broken provider (this test), candidates include
        both users — which is the bug we're exposing.
        """
        query = _make_llm_query(QUERY_TEXT)

        _, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id=ALICE_USER_ID,
        )

        # If provider pre-filter worked, candidate_count would be 1.
        # With broken provider, it's 2. The injector should still
        # only inject 1 after its own user_id check.
        #
        # This assertion checks the final injected count (defense
        # in depth) rather than candidate_count (which reflects the
        # provider's output).
        self.assertEqual(
            diagnostics["injected_count"], 1,
            "After all filtering layers, only 1 memory "
            "(correct user) should survive.",
        )


# ------------------------------------------------------------------
# Section 3: Kernel-shared identity forms
#
# Tests that the isolation holds for the __kernel_shared naming
# convention used in production.
# ------------------------------------------------------------------


class TestKernelSharedIdentityIsolation(unittest.TestCase):
    """Verify isolation with the kernel-shared user_id format
    (e.g., 'alice__kernel_shared')."""

    def setUp(self) -> None:
        self.provider = LeakyMemoryProvider()

        # Alice's kernel-shared memory
        self.provider.seed(
            content="Alice prefers dark mode and Python",
            metadata={
                "user_id": "alice__kernel_shared",
                "owner_agent": PROFILE_AGENT,
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        # Bob's kernel-shared memory
        self.provider.seed(
            content="Bob prefers light mode and Rust",
            metadata={
                "user_id": "bob__kernel_shared",
                "owner_agent": PROFILE_AGENT,
                "sharing_policy": "shared",
                "memory_type": "profile",
            },
        )

        self.injector = _build_context_injector(self.provider)

    def test_kernel_shared_alice_excludes_bob(self):
        """Under the __kernel_shared naming convention, Alice's
        injection must not include Bob's memory."""
        query = _make_llm_query("What are my preferences?")

        result_query, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id="alice__kernel_shared",
        )

        injected_count = diagnostics.get("injected_count", 0)
        self.assertGreater(injected_count, 0)

        injected_content = result_query.messages[0]["content"]

        # Bob's content must NOT appear
        self.assertNotIn(
            "Bob",
            injected_content,
            f"CROSS-USER LEAKAGE with __kernel_shared identity: "
            f"Bob's memory leaked into Alice's context. "
            f"Content: {injected_content!r}",
        )
        self.assertNotIn(
            "Rust",
            injected_content,
            f"CROSS-USER LEAKAGE: Bob's Rust preference "
            f"leaked into Alice's context.",
        )
        self.assertNotIn(
            "light mode",
            injected_content,
            "Bob's light mode preference must not appear "
            "in Alice's injection.",
        )

        # Alice's content SHOULD appear
        self.assertIn(
            "Alice",
            injected_content,
            "Alice's memory should be injected.",
        )

    def test_kernel_shared_injected_count_is_one(self):
        """Only Alice's memory should be in the injected set."""
        query = _make_llm_query("What are my preferences?")

        _, diagnostics = self.injector.inject(
            agent_name=TEST_AGENT,
            query=query,
            user_id="alice__kernel_shared",
        )

        self.assertEqual(
            diagnostics["injected_count"], 1,
            f"Expected 1 injected memory (Alice's), got "
            f"{diagnostics['injected_count']}. Cross-user "
            f"leakage detected with __kernel_shared identity.",
        )


# ------------------------------------------------------------------
# Section 4: Provider-level cross-user isolation with get_all
#
# Verifies the provider's get_all call passes the correct filter
# for cross-agent shared retrieval (the _retrieve_shared_memories
# path in ContextInjector).
# ------------------------------------------------------------------


class TestProviderSharedRetrievalFilter(unittest.TestCase):
    """When the ContextInjector's _retrieve_shared_memories issues
    a query with sharing_policy='shared' and user_id, the provider
    must still enforce user_id at the get_all filter level."""

    def test_shared_retrieval_get_all_has_user_filter(self):
        """For cross-agent shared retrieval, get_all must receive
        filters={"user_id": resolved_user_id}."""
        provider, mock_client = _create_provider_with_mock()

        # This is what _retrieve_shared_memories sends:
        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 20,  # 4× over-fetch
                "user_id": ALICE_USER_ID,
                "sharing_policy": "shared",
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        mock_client.get_all.assert_called_once()
        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertEqual(
            filters.get("user_id"), ALICE_USER_ID,
            "Cross-agent shared retrieval must pass the "
            "resolved user_id in filters to get_all().",
        )
        # Ensure no top-level user_id
        self.assertNotIn(
            "user_id", kwargs,
            "user_id must not be a top-level kwarg.",
        )

    def test_own_retrieval_get_all_has_user_filter(self):
        """For own-memory retrieval (no sharing_policy), get_all
        must still receive filters={"user_id": ...}."""
        provider, mock_client = _create_provider_with_mock()

        # This is what the ContextInjector's own-memory path sends:
        query = MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": QUERY_TEXT,
                "k": 5,
                "user_id": ALICE_USER_ID,
                "agent_name": TEST_AGENT,
            },
        )
        provider.retrieve_memory(query)

        _, kwargs = mock_client.get_all.call_args
        filters = kwargs.get("filters", {})

        self.assertEqual(
            filters.get("user_id"), ALICE_USER_ID,
            "Own-memory retrieval must also pass user_id "
            "in the filters dict.",
        )


if __name__ == "__main__":
    unittest.main()
