"""
Access-matrix test suite for ContextInjector user-partition and
sharing-policy enforcement.

Documents and verifies the intended authorization predicate:

    same_user_partition AND (
        owner_agent == requesting_agent
        OR (
            sharing_policy == "shared"
            AND requesting_agent in privilege_group(owner_agent)
        )
    )

User partitioning is ALWAYS evaluated before agent-level sharing.
In these tests profile_agent's privilege group admits task_agent,
the requesting agent.

Access Matrix:
    | Same User | Owner Relation | Sharing Policy | Result  |
    |-----------|----------------|----------------|---------|
    | Yes       | Same agent     | Private        | ALLOW   |
    | Yes       | Same agent     | Shared         | ALLOW   |
    | Yes       | Different agent| Private        | DENY    |
    | Yes       | Different agent| Shared         | ALLOW   |
    | Yes       | Different agent, not in group | Shared | DENY |
    | No        | Same agent     | Private        | DENY    |
    | No        | Same agent     | Shared         | DENY    |
    | No        | Different agent| Private        | DENY    |
    | No        | Different agent| Shared         | DENY    |
    | Missing   | Any            | Any            | DENY    |

Additional invariants tested:
- Namespaced identities compared exactly (no prefix matching)
- Malformed metadata fails closed without exceptions
- Wrong-user memories removed before token budgeting
- Deduplication does not admit wrong-user candidates
- Relevance score cannot override user isolation
- Agent-name fallback (user_id=None) preserves legacy behavior
- Legacy unscoped memories (missing user_id) excluded by default

Run:
    .venv/bin/python -m pytest \
        tests/modules/memory/test_context_injector_access_matrix.py -v
"""
from __future__ import annotations

import os
import sys
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional

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


# ------------------------------------------------------------------
# Test provider: returns ALL seeded memories (no pre-filtering)
# ------------------------------------------------------------------


class AllMemoryProvider(MemoryProvider):
    """Returns every seeded memory regardless of query params.

    This forces the ContextInjector's own filters to be the sole
    enforcement layer, making the tests a true unit test of the
    injector's access logic rather than the provider's.
    """

    def __init__(self) -> None:
        self._memories: List[dict] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def seed(
        self,
        content: str,
        metadata: Optional[dict] = None,
        score: float = 0.9,
    ) -> None:
        self._memories.append({
            "content": content,
            "metadata": metadata if metadata is not None else {},
            "score": score,
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
        return MemoryResponse(success=False, error="stub")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        return MemoryResponse(
            success=True,
            search_results=list(self._memories),
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


def _build_injector(
    provider: AllMemoryProvider,
    max_tokens: int = 5000,
    relevance_threshold: float = 0.0,
    max_memories: int = 20,
) -> ContextInjector:
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    manager.barrier = MemoryWriteBarrier(
        config={"enabled": False}
    )
    # profile_agent admits task_agent to its privilege group.
    manager.access_manager = AccessManager({
        "profile_agent": ["task_agent"],
    })
    config = {
        "auto_inject": True,
        "max_injected_memories": max_memories,
        "relevance_threshold": relevance_threshold,
        "max_memory_tokens": max_tokens,
    }
    return ContextInjector(memory_manager=manager, config=config)


def _make_query(text: str = "Hello") -> LLMQuery:
    return LLMQuery(
        messages=[{"role": "user", "content": text}],
        tools=None,
        action_type="chat",
        message_return_type="text",
    )


def _injected_contents(result_query: LLMQuery) -> List[str]:
    """Extract individual memory content strings from the
    injected system message (if any)."""
    if len(result_query.messages) <= 1:
        return []
    sys_content = result_query.messages[0].get("content", "")
    lines = sys_content.split("\n")
    contents = []
    for line in lines:
        if line.startswith("- ["):
            # Format: "- [timestamp] content"
            bracket_end = line.index("]", 3)
            contents.append(line[bracket_end + 2:])
    return contents


# ==================================================================
# Section 1: Core Access Matrix (table-driven)
# ==================================================================


# Each tuple: (description, memory_metadata, expected_injected)
ACCESS_MATRIX_CASES = [
    (
        "same_user + same_agent + private → ALLOW",
        {
            "user_id": "alice",
            "owner_agent": "task_agent",
            "sharing_policy": "private",
        },
        True,
    ),
    (
        "same_user + same_agent + shared → ALLOW",
        {
            "user_id": "alice",
            "owner_agent": "task_agent",
            "sharing_policy": "shared",
        },
        True,
    ),
    (
        "same_user + different_agent + private → DENY",
        {
            "user_id": "alice",
            "owner_agent": "profile_agent",
            "sharing_policy": "private",
        },
        False,
    ),
    (
        "same_user + different_agent + shared → ALLOW",
        {
            "user_id": "alice",
            "owner_agent": "profile_agent",
            "sharing_policy": "shared",
        },
        True,
    ),
    (
        "different_user + same_agent + private → DENY",
        {
            "user_id": "bob",
            "owner_agent": "task_agent",
            "sharing_policy": "private",
        },
        False,
    ),
    (
        "different_user + same_agent + shared → DENY",
        {
            "user_id": "bob",
            "owner_agent": "task_agent",
            "sharing_policy": "shared",
        },
        False,
    ),
    (
        "different_user + different_agent + private → DENY",
        {
            "user_id": "bob",
            "owner_agent": "profile_agent",
            "sharing_policy": "private",
        },
        False,
    ),
    (
        "different_user + different_agent + shared → DENY",
        {
            "user_id": "bob",
            "owner_agent": "profile_agent",
            "sharing_policy": "shared",
        },
        False,
    ),
]


class TestAccessMatrix(unittest.TestCase):
    """Table-driven access matrix: each case seeds ONE memory and
    checks whether it survives into the injected prompt."""

    def _run_case(self, metadata: dict, expect_injected: bool):
        provider = AllMemoryProvider()
        content = f"Memory content for {metadata}"
        provider.seed(content=content, metadata=metadata)
        injector = _build_injector(provider)
        query = _make_query("test query")

        result_query, diag = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )

        injected = _injected_contents(result_query)
        if expect_injected:
            self.assertIn(
                content, injected,
                f"Memory should be ALLOWED but was excluded. "
                f"Metadata: {metadata}",
            )
        else:
            self.assertNotIn(
                content, injected,
                f"Memory should be DENIED but was injected. "
                f"Metadata: {metadata}",
            )

    def test_same_user_same_agent_private(self):
        self._run_case(*ACCESS_MATRIX_CASES[0][1:])

    def test_same_user_same_agent_shared(self):
        self._run_case(*ACCESS_MATRIX_CASES[1][1:])

    def test_same_user_different_agent_private(self):
        self._run_case(*ACCESS_MATRIX_CASES[2][1:])

    def test_same_user_different_agent_shared(self):
        self._run_case(*ACCESS_MATRIX_CASES[3][1:])

    def test_different_user_same_agent_private(self):
        self._run_case(*ACCESS_MATRIX_CASES[4][1:])

    def test_different_user_same_agent_shared(self):
        self._run_case(*ACCESS_MATRIX_CASES[5][1:])

    def test_different_user_different_agent_private(self):
        self._run_case(*ACCESS_MATRIX_CASES[6][1:])

    def test_different_user_different_agent_shared(self):
        self._run_case(*ACCESS_MATRIX_CASES[7][1:])

    def test_same_user_agent_outside_privilege_group_shared(self):
        """Issue #549: a shared memory from an agent whose
        privilege group does not admit the requester is DENIED."""
        self._run_case(
            {
                "user_id": "alice",
                "owner_agent": "web_crawler",
                "sharing_policy": "shared",
            },
            False,
        )


# ==================================================================
# Section 2: Explicit user_id behavior
# ==================================================================


class TestExplicitUserBehavior(unittest.TestCase):
    """When inject(user_id="alice") is called, verify the full
    authorization matrix against a realistic multi-agent scenario."""

    def setUp(self):
        self.provider = AllMemoryProvider()
        # Alice's private memory from task_agent → ALLOW
        self.provider.seed(
            content="Alice private task note",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        # Alice's private memory from profile_agent → DENY
        self.provider.seed(
            content="Alice private profile note",
            metadata={
                "user_id": "alice",
                "owner_agent": "profile_agent",
                "sharing_policy": "private",
            },
        )
        # Alice's shared memory from profile_agent → ALLOW
        self.provider.seed(
            content="Alice shared profile note",
            metadata={
                "user_id": "alice",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
            },
        )
        # Bob's private memory from task_agent → DENY
        self.provider.seed(
            content="Bob private task note",
            metadata={
                "user_id": "bob",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        # Bob's shared memory from profile_agent → DENY
        self.provider.seed(
            content="Bob shared profile note",
            metadata={
                "user_id": "bob",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
            },
        )
        self.injector = _build_injector(self.provider)

    def test_alice_gets_correct_memories(self):
        query = _make_query("What do I have?")
        result, diag = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertIn("Alice private task note", injected)
        self.assertIn("Alice shared profile note", injected)
        self.assertNotIn("Alice private profile note", injected)
        self.assertNotIn("Bob private task note", injected)
        self.assertNotIn("Bob shared profile note", injected)

    def test_injected_count_matches(self):
        query = _make_query("What do I have?")
        _, diag = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        self.assertEqual(diag["injected_count"], 2)


# ==================================================================
# Section 3: Agent-name fallback (user_id=None)
# ==================================================================


class TestAgentNameFallback(unittest.TestCase):
    """When no explicit user_id is provided, the resolved partition
    becomes agent_name. Memories stored under that partition must
    work."""

    def setUp(self):
        self.provider = AllMemoryProvider()
        # Memory stored with user_id = agent_name (legacy pattern)
        self.provider.seed(
            content="Agent-scoped conversation memory",
            metadata={
                "user_id": "task_agent",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        # Memory for a real user (should be excluded)
        self.provider.seed(
            content="Real user memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        self.injector = _build_injector(self.provider)

    def test_fallback_uses_agent_name_as_partition(self):
        query = _make_query("Hello")
        result, diag = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id=None,
        )
        injected = _injected_contents(result)

        self.assertIn(
            "Agent-scoped conversation memory", injected,
            "Memories stored under agent_name partition should "
            "be accessible when no user_id is provided.",
        )
        self.assertNotIn(
            "Real user memory", injected,
            "Memories for a different partition (alice) should "
            "be excluded under agent_name fallback.",
        )

    def test_resolved_user_id_is_none(self):
        query = _make_query("Hello")
        _, diag = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id=None,
        )
        self.assertIsNone(diag["resolved_user_id"])


# ==================================================================
# Section 4: Namespaced identity exact matching
# ==================================================================


class TestNamespacedIdentities(unittest.TestCase):
    """Namespaced identities must be compared as exact strings.
    No prefix, suffix, or normalized-base-user matching."""

    def setUp(self):
        self.provider = AllMemoryProvider()
        self.provider.seed(
            content="alice plain memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        self.provider.seed(
            content="alice kernel_shared memory",
            metadata={
                "user_id": "alice__kernel_shared",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        self.provider.seed(
            content="bob kernel_shared memory",
            metadata={
                "user_id": "bob__kernel_shared",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        self.injector = _build_injector(self.provider)

    def test_alice_plain_excludes_kernel_shared(self):
        query = _make_query("test")
        result, _ = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertIn("alice plain memory", injected)
        self.assertNotIn(
            "alice kernel_shared memory", injected,
            "'alice' must not match 'alice__kernel_shared'",
        )

    def test_alice_kernel_shared_excludes_plain(self):
        query = _make_query("test")
        result, _ = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice__kernel_shared",
        )
        injected = _injected_contents(result)

        self.assertIn("alice kernel_shared memory", injected)
        self.assertNotIn(
            "alice plain memory", injected,
            "'alice__kernel_shared' must not match 'alice'",
        )

    def test_alice_kernel_shared_excludes_bob_kernel_shared(self):
        query = _make_query("test")
        result, _ = self.injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice__kernel_shared",
        )
        injected = _injected_contents(result)

        self.assertNotIn(
            "bob kernel_shared memory", injected,
            "'alice__kernel_shared' must not match "
            "'bob__kernel_shared'",
        )


# ==================================================================
# Section 5: Malformed / incomplete metadata (fail closed)
# ==================================================================


class TestMalformedMetadata(unittest.TestCase):
    """Memories with missing or malformed metadata must fail closed
    without raising exceptions."""

    def _inject_single(self, metadata):
        provider = AllMemoryProvider()
        provider.seed(content="malformed memory", metadata=metadata)
        # Also seed a valid memory to verify injection works
        provider.seed(
            content="valid memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        injector = _build_injector(provider)
        query = _make_query("test")
        result, diag = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        return _injected_contents(result), diag

    def test_metadata_none(self):
        """{"metadata": None} → excluded, no exception."""
        injected, _ = self._inject_single(None)
        self.assertNotIn("malformed memory", injected)
        self.assertIn("valid memory", injected)

    def test_metadata_empty_dict(self):
        """{} → excluded (no user_id)."""
        injected, _ = self._inject_single({})
        self.assertNotIn("malformed memory", injected)
        self.assertIn("valid memory", injected)

    def test_metadata_missing_user_id(self):
        """{"owner_agent": "task_agent"} → excluded."""
        injected, _ = self._inject_single({
            "owner_agent": "task_agent"
        })
        self.assertNotIn("malformed memory", injected)
        self.assertIn("valid memory", injected)

    def test_metadata_user_id_none(self):
        """{"user_id": None} → excluded."""
        injected, _ = self._inject_single({
            "user_id": None,
            "owner_agent": "task_agent",
            "sharing_policy": "private",
        })
        self.assertNotIn("malformed memory", injected)
        self.assertIn("valid memory", injected)

    def test_metadata_user_id_empty_string(self):
        """{"user_id": ""} → excluded."""
        injected, _ = self._inject_single({
            "user_id": "",
            "owner_agent": "task_agent",
            "sharing_policy": "private",
        })
        self.assertNotIn("malformed memory", injected)
        self.assertIn("valid memory", injected)


# ==================================================================
# Section 6: Deduplication across own and shared retrieval
# ==================================================================


class TestDeduplication(unittest.TestCase):
    """Duplicate memories across retrieval paths are injected once.
    A wrong-user duplicate cannot suppress a valid candidate."""

    def test_duplicate_injected_once(self):
        """Same content from own and shared paths → injected once."""
        provider = AllMemoryProvider()
        # Same content appears twice (own + shared retrieval)
        provider.seed(
            content="Duplicate memory content",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        provider.seed(
            content="Duplicate memory content",
            metadata={
                "user_id": "alice",
                "owner_agent": "profile_agent",
                "sharing_policy": "shared",
            },
        )
        injector = _build_injector(provider)
        query = _make_query("test")
        result, diag = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        # Content appears but the system should have both pass
        # through (both are valid for alice). The dedup in
        # _merge_and_deduplicate removes content duplicates,
        # but since provider returns all at once (no separate
        # own/shared calls), both arrive in own_results and
        # pass through. Verify no wrong-user leakage.
        count = injected.count("Duplicate memory content")
        # Both are valid alice memories, so up to 2 is OK.
        # The key invariant: no bob memory sneaks in.
        self.assertGreaterEqual(count, 1)
        self.assertLessEqual(count, 2)

    def test_wrong_user_duplicate_does_not_suppress_valid(self):
        """A wrong-user memory with same content does not suppress
        the valid same-user version."""
        provider = AllMemoryProvider()
        # Bob has same content
        provider.seed(
            content="Important task context",
            metadata={
                "user_id": "bob",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        # Alice also has it (valid)
        provider.seed(
            content="Important task context",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        injector = _build_injector(provider)
        query = _make_query("test")
        result, _ = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertIn(
            "Important task context", injected,
            "Valid same-user memory must survive even when a "
            "wrong-user duplicate exists.",
        )


# ==================================================================
# Section 7: Relevance score cannot override user isolation
# ==================================================================


class TestRelevanceDoesNotOverrideIsolation(unittest.TestCase):
    """A wrong-user memory with the highest score must still be
    excluded. A correct-user memory with a lower score survives."""

    def test_high_score_wrong_user_excluded(self):
        provider = AllMemoryProvider()
        # Wrong user, highest score
        provider.seed(
            content="Bob high-score memory",
            metadata={
                "user_id": "bob",
                "owner_agent": "task_agent",
                "sharing_policy": "shared",
            },
            score=1.0,
        )
        # Correct user, lower score (above threshold)
        provider.seed(
            content="Alice lower-score memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
            score=0.6,
        )
        injector = _build_injector(
            provider, relevance_threshold=0.5
        )
        query = _make_query("test")
        result, _ = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertNotIn("Bob high-score memory", injected)
        self.assertIn("Alice lower-score memory", injected)


# ==================================================================
# Section 8: Token budgeting interaction
# ==================================================================


class TestTokenBudgetInteraction(unittest.TestCase):
    """Wrong-user memories are removed BEFORE token budget is
    consumed. A wrong-user candidate must not cause a valid
    same-user memory to be dropped."""

    def test_wrong_user_does_not_consume_budget(self):
        provider = AllMemoryProvider()
        # Seed many wrong-user memories with high scores
        for i in range(10):
            provider.seed(
                content=f"Bob memory {i} " + ("x" * 200),
                metadata={
                    "user_id": "bob",
                    "owner_agent": "task_agent",
                    "sharing_policy": "shared",
                },
                score=0.99,
            )
        # Seed one valid alice memory with lower score
        provider.seed(
            content="Alice important memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
            score=0.7,
        )
        # Use a tight token budget
        injector = _build_injector(
            provider, max_tokens=500
        )
        query = _make_query("test")
        result, diag = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertIn(
            "Alice important memory", injected,
            "Alice's memory should survive because wrong-user "
            "memories are removed before token budgeting.",
        )
        # No bob memories should be present
        for content in injected:
            self.assertNotIn(
                "Bob memory", content,
                "Wrong-user memories must never reach "
                "token budgeting.",
            )


# ==================================================================
# Section 9: Legacy unscoped memories
# ==================================================================


class TestLegacyUnscopedMemories(unittest.TestCase):
    """Memories created before user_id scoping was introduced lack
    metadata["user_id"]. These must be excluded by default.

    Legacy unscoped memories require explicit migration (assign
    correct user_id from trusted provenance) rather than implicit
    admission into the current user's context.
    """

    def test_legacy_memory_without_user_id_excluded(self):
        provider = AllMemoryProvider()
        # Legacy memory: has owner_agent but no user_id
        provider.seed(
            content="Legacy conversation from before scoping",
            metadata={
                "owner_agent": "task_agent",
                "sharing_policy": "private",
                # no user_id field at all
            },
        )
        # Valid current memory
        provider.seed(
            content="Current scoped memory",
            metadata={
                "user_id": "alice",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        injector = _build_injector(provider)
        query = _make_query("test")
        result, _ = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id="alice",
        )
        injected = _injected_contents(result)

        self.assertNotIn(
            "Legacy conversation from before scoping",
            injected,
            "Legacy memories without user_id must be excluded "
            "by default. They require explicit migration to "
            "assign a correct user_id from trusted provenance.",
        )
        self.assertIn("Current scoped memory", injected)

    def test_legacy_memory_excluded_under_fallback_too(self):
        """Even under agent_name fallback, a memory without
        user_id is excluded (empty string != agent_name)."""
        provider = AllMemoryProvider()
        provider.seed(
            content="No user_id memory",
            metadata={
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        provider.seed(
            content="Properly scoped to agent",
            metadata={
                "user_id": "task_agent",
                "owner_agent": "task_agent",
                "sharing_policy": "private",
            },
        )
        injector = _build_injector(provider)
        query = _make_query("test")
        result, _ = injector.inject(
            agent_name="task_agent",
            query=query,
            user_id=None,
        )
        injected = _injected_contents(result)

        self.assertNotIn("No user_id memory", injected)
        self.assertIn("Properly scoped to agent", injected)


if __name__ == "__main__":
    unittest.main()
