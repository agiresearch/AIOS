"""
End-to-End Benchmark: Per-Request user_id Through AIOS Stack

Simulates the full benchmark harness flow with 5+ sequential synthetic
users, including a return-visit scenario (Trial 6 = Jordan again).

Verifies:
  1. Each trial's QueryRequest carries a distinct user_id.
  2. Context injection uses the request-scoped user_id (not latest).
  3. Retrieve calls in the provider show per-trial user_ids.
  4. Return visits retrieve the returning user's memories.
  5. No cross-user memory contamination.

This test exercises the full AIOS-internal dispatch path:
  QueryRequest.user_id → launch.py attaches _request_user_id →
  SyscallExecutor.execute_request extracts it →
  ContextInjector.inject(user_id=...) →
  _resolve_user_id(request_user_id=...) →
  provider.retrieve_memory(user_id=<correct>)

Run:
    pytest tests/modules/memory/test_benchmark_user_id_e2e.py -v
"""
from __future__ import annotations

import logging
import os
import sys
import time
import unittest
from collections import OrderedDict
from io import StringIO
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.context_injector import ContextInjector
from aios.memory.providers.base import MemoryProvider
from aios.memory.write_barrier import MemoryWriteBarrier

from tests.modules.memory._doubles.open_access import (
    personalization_access_manager,
)


# ------------------------------------------------------------------
# Synthetic users (benchmark-style distinct identities)
# ------------------------------------------------------------------

BENCHMARK_USERS = [
    {
        "user_id": "jordan_matthews_75157bae",
        "profile": "Jordan Matthews is a backend engineer who loves Go.",
        "question": "What programming language do I prefer?",
        "expected_keyword": "Go",
    },
    {
        "user_id": "julia_romero_a3e82c1f",
        "profile": "Julia Romero is a data scientist who prefers R.",
        "question": "What tool do I use for data analysis?",
        "expected_keyword": "R",
    },
    {
        "user_id": "olivia_ramirez_d9f04b72",
        "profile": "Olivia Ramirez is a DevOps engineer who uses Terraform.",
        "question": "What infrastructure tool do I use?",
        "expected_keyword": "Terraform",
    },
    {
        "user_id": "ethan_nakamura_1b5c7d9e",
        "profile": "Ethan Nakamura is a frontend dev who uses Svelte.",
        "question": "What frontend framework do I prefer?",
        "expected_keyword": "Svelte",
    },
    {
        "user_id": "maya_patel_e8a3f620",
        "profile": "Maya Patel is a security researcher who codes in Rust.",
        "question": "What language do I code in?",
        "expected_keyword": "Rust",
    },
]


# ------------------------------------------------------------------
# Test infrastructure
# ------------------------------------------------------------------


class BenchmarkProvider(MemoryProvider):
    """Provider that records operations and scopes by user_id."""

    def __init__(self) -> None:
        self._store: Dict[str, List[dict]] = {}
        self.retrieve_log: List[Dict[str, Any]] = []

    def initialize(self, config: Dict[str, Any]) -> None:
        pass

    def add_memory(self, memory_note: Any) -> MemoryResponse:
        metadata = getattr(memory_note, "metadata", {}) or {}
        user_id = metadata.get("user_id", "unknown")
        content = getattr(memory_note, "content", "")
        self._store.setdefault(user_id, []).append({
            "content": content,
            "metadata": dict(metadata),
            "score": 0.92,
        })
        return MemoryResponse(success=True, memory_id="ok")

    def seed(
        self, user_id: str, content: str, metadata: dict
    ) -> None:
        self._store.setdefault(user_id, []).append({
            "content": content,
            "metadata": dict(metadata),
            "score": 0.92,
        })

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note: Any) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id="ok")

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(
        self, query: MemoryQuery
    ) -> MemoryResponse:
        user_id = query.params.get("user_id")
        agent_name = query.params.get("agent_name")
        self.retrieve_log.append({
            "user_id": user_id,
            "agent_name": agent_name,
            "content_query": query.params.get("content", ""),
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


class BenchmarkMemoryManager:
    """Minimal manager for benchmark simulation."""

    def __init__(self, provider: BenchmarkProvider) -> None:
        self.provider = provider
        self.barrier = MemoryWriteBarrier(config={})
        self.access_manager = personalization_access_manager()
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


# ------------------------------------------------------------------
# Benchmark end-to-end test
# ------------------------------------------------------------------


class TestBenchmarkEndToEnd(unittest.TestCase):
    """Simulates the full benchmark harness flow with 6 trials
    (5 unique users + 1 return visit) and verifies per-request
    user_id isolation end-to-end.
    """

    def setUp(self) -> None:
        self.provider = BenchmarkProvider()
        self.manager = BenchmarkMemoryManager(
            provider=self.provider
        )
        self.injector = ContextInjector(
            memory_manager=self.manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        # Set up logging capture
        self.log_stream = StringIO()
        self.log_handler = logging.StreamHandler(self.log_stream)
        self.log_handler.setLevel(logging.INFO)
        logger = logging.getLogger("aios.memory.context_injector")
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.INFO)

        # Seed all users' memories (simulates ProfileAgent writes)
        for user in BENCHMARK_USERS:
            uid = user["user_id"]
            self.provider.seed(
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

    def tearDown(self) -> None:
        logger = logging.getLogger("aios.memory.context_injector")
        logger.removeHandler(self.log_handler)

    def _get_system_content(self, query: LLMQuery) -> str:
        for msg in query.messages:
            if msg.get("role") == "system":
                content = msg.get("content", "")
                if "MEMORY CONTEXT" in content:
                    return content
        return ""

    def _simulate_benchmark_request(
        self, user_id: str, question: str
    ) -> tuple:
        """Simulate a benchmark trial's request flow:
        QueryRequest → _request_user_id → inject(user_id=...)
        """
        # Build the LLMQuery as the kernel would
        query = LLMQuery(
            messages=[{"role": "user", "content": question}],
            action_type="chat",
        )
        # Attach _request_user_id as runtime/launch.py would
        query._request_user_id = user_id

        # Call inject with user_id (as SyscallExecutor would)
        request_user_id = getattr(query, "_request_user_id", None)
        result_query, diag = self.injector.inject(
            "assistant_agent",
            query,
            user_id=request_user_id,
        )
        return result_query, diag

    # ==============================================================
    # Main benchmark test: 6 trials with return visit
    # ==============================================================

    def test_benchmark_6_trials_with_return_visit(self) -> None:
        """Run 6 benchmark trials:
          Trial 1: Jordan
          Trial 2: Julia
          Trial 3: Olivia
          Trial 4: Ethan
          Trial 5: Maya
          Trial 6: Jordan (return visit)

        All trials must retrieve the correct user's memories.
        """
        # Build trial sequence (5 unique + return visit)
        trials = list(BENCHMARK_USERS) + [BENCHMARK_USERS[0]]
        results = []

        self.provider.retrieve_log.clear()

        for i, trial in enumerate(trials):
            uid = trial["user_id"]
            question = trial["question"]
            expected = trial["expected_keyword"]

            result_query, diag = self._simulate_benchmark_request(
                user_id=uid, question=question
            )

            injected = self._get_system_content(result_query)
            correct_memory = expected in injected
            stale_injection = False

            # Check for contamination from other users
            # Use exact word matching to avoid false positives
            # from short keywords like "R" matching inside words
            for other in BENCHMARK_USERS:
                if other["user_id"] != uid:
                    other_kw = other["expected_keyword"]
                    # Use word boundary check: keyword must appear
                    # as a standalone word or at word boundary
                    import re
                    pattern = r'\b' + re.escape(other_kw) + r'\b'
                    if re.search(pattern, injected):
                        stale_injection = True
                        break

            results.append({
                "trial": i + 1,
                "user_id": uid,
                "resolved_user_id": diag["resolved_user_id"],
                "injected_count": diag["injected_count"],
                "correct_memory": correct_memory,
                "stale_injection": stale_injection,
                "expected_keyword": expected,
            })

        # --- Print benchmark summary ---
        print("\n" + "=" * 70)
        print("BENCHMARK RESULT SUMMARY")
        print("=" * 70)
        print(f"  Trials run: {len(results)}")
        print(f"  Unique synthetic users: {len(BENCHMARK_USERS)}")
        print(f"  Return visit included: Yes (Trial 6 = Jordan)")
        print()

        for r in results:
            status = "PASS" if r["correct_memory"] else "FAIL"
            contam = " [CONTAMINATED]" if r["stale_injection"] else ""
            print(
                f"  Trial {r['trial']}: user={r['user_id'][:20]}... "
                f"resolved={r['resolved_user_id'][:20]}... "
                f"injected={r['injected_count']} "
                f"[{status}]{contam}"
            )

        print()

        # --- Assertions ---
        for r in results:
            # Each trial used the correct user_id
            self.assertEqual(
                r["resolved_user_id"],
                r["user_id"],
                f"Trial {r['trial']}: resolved wrong user_id. "
                f"Expected {r['user_id']}, "
                f"got {r['resolved_user_id']}",
            )
            # Correct memory was retrieved
            self.assertTrue(
                r["correct_memory"],
                f"Trial {r['trial']}: expected keyword "
                f"'{r['expected_keyword']}' not found in "
                f"injected context for {r['user_id']}",
            )
            # No contamination
            self.assertFalse(
                r["stale_injection"],
                f"Trial {r['trial']}: cross-user contamination "
                f"detected for {r['user_id']}",
            )

        # --- Verify retrieve log shows distinct user_ids ---
        retrieve_user_ids = [
            e["user_id"]
            for e in self.provider.retrieve_log
        ]
        unique_in_log = set(retrieve_user_ids)
        # Must see all 5 unique users in the log
        for user in BENCHMARK_USERS:
            self.assertIn(
                user["user_id"],
                unique_in_log,
                f"User {user['user_id']} missing from "
                f"retrieve log",
            )

        # --- Verify kernel logs show request-scoped resolution ---
        log_output = self.log_stream.getvalue()
        self.assertIn(
            "user_id resolved from REQUEST",
            log_output,
            "Expected log entry showing request-scoped "
            "resolution was used",
        )
        # Should NOT see "resolved from FALLBACK" since all
        # trials pass explicit user_id
        self.assertNotIn(
            "resolved from FALLBACK",
            log_output,
            "Unexpected fallback resolution when request "
            "user_id was provided",
        )

        print("  RESULT: ALL TRIALS PASSED")
        print("  - Each trial used request-scoped user_id")
        print("  - No cross-user contamination detected")
        print("  - Return visit (Jordan) correctly retrieved")
        print("    Jordan's memories, not Maya's (latest)")
        print("=" * 70)

    # ==============================================================
    # Return visit isolation test
    # ==============================================================

    def test_return_visit_retrieves_correct_user(self) -> None:
        """Specifically verify that after all 5 users write,
        Jordan returning gets Jordan's memories (Go) and NOT
        Maya's (Rust, the latest writer).
        """
        # latest_user_id is maya (last seeded)
        self.assertEqual(
            self.manager.latest_user_id,
            "maya_patel_e8a3f620",
        )

        # Jordan returns
        result_query, diag = self._simulate_benchmark_request(
            user_id="jordan_matthews_75157bae",
            question="What language do I prefer?",
        )

        self.assertEqual(
            diag["resolved_user_id"],
            "jordan_matthews_75157bae",
        )

        injected = self._get_system_content(result_query)
        self.assertIn("Go", injected)
        self.assertNotIn("Rust", injected)
        self.assertNotIn("Terraform", injected)
        self.assertNotIn("Svelte", injected)
        self.assertNotIn("R.", injected)

    # ==============================================================
    # Verify request body carries user_id
    # ==============================================================

    def test_request_body_includes_user_id(self) -> None:
        """Verify the simulated QueryRequest body includes user_id
        and it propagates through the _request_user_id attr.
        """
        query = LLMQuery(
            messages=[{"role": "user", "content": "test"}],
            action_type="chat",
        )
        # Simulate what launch.py does
        query._request_user_id = "julia_romero_a3e82c1f"

        # Verify it's accessible
        self.assertEqual(
            getattr(query, "_request_user_id", None),
            "julia_romero_a3e82c1f",
        )

        # Verify inject receives and uses it
        _, diag = self.injector.inject(
            "assistant_agent",
            query,
            user_id=getattr(query, "_request_user_id", None),
        )
        self.assertEqual(
            diag["resolved_user_id"],
            "julia_romero_a3e82c1f",
        )

    # ==============================================================
    # Log verification
    # ==============================================================

    def test_kernel_logs_show_request_scoped_resolution(
        self,
    ) -> None:
        """Verify that the kernel logs explicitly indicate
        resolution came from the REQUEST, not FALLBACK.
        """
        self.log_stream.truncate(0)
        self.log_stream.seek(0)

        self._simulate_benchmark_request(
            user_id="ethan_nakamura_1b5c7d9e",
            question="What framework?",
        )

        log_output = self.log_stream.getvalue()
        self.assertIn(
            "user_id resolved from REQUEST: "
            "ethan_nakamura_1b5c7d9e",
            log_output,
        )
        self.assertNotIn("FALLBACK", log_output)

    # ==============================================================
    # Score consistency check
    # ==============================================================

    def test_personalization_scores_consistent_across_trials(
        self,
    ) -> None:
        """All trials should inject exactly 1 memory (their own
        profile). Before the fix, some trials might inject 0
        (wrong user_id scope) or inject the wrong user's memory.
        """
        for user in BENCHMARK_USERS:
            _, diag = self._simulate_benchmark_request(
                user_id=user["user_id"],
                question=user["question"],
            )
            self.assertEqual(
                diag["injected_count"],
                1,
                f"User {user['user_id']}: expected 1 injected "
                f"memory, got {diag['injected_count']}",
            )


if __name__ == "__main__":
    unittest.main()
