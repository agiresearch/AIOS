"""
Preservation property tests for the memory write-barrier bugfix.

These tests capture the BASELINE behaviour of the unfixed kernel for
inputs that do **not** trigger the write-before-read race
(``isBugCondition(X) == false``).  The fix MUST preserve every one of
these behaviours unchanged.

The seven preservation cases below correspond to clauses 3.1-3.7 in
``.kiro/specs/memory-write-barrier/bugfix.md`` and to Property 2
(Preservation - Non-Bug Inputs Unchanged) in
``.kiro/specs/memory-write-barrier/design.md``:

- 2a No-user_id Retrieval Preservation        (Clause 3.3)
- 2b Unrelated user_id Preservation           (Clause 3.2)
- 2c Drained State Preservation               (Clauses 3.1, 3.4, 3.6, 3.7)
- 2d InHouseProvider Preservation             (Clause 3.5)
- 2e ZepProvider Preservation                 (Clause 3.5)
- 2f auto_inject=false Preservation           (Clause 3.5)
- 2g Single-Agent Serial Preservation         (Clause 3.6)

EXPECTED OUTCOME on the UNFIXED kernel: every case PASSES.  When the
fix lands, these tests continue to pass - they are the regression
guard for the fast path.

----------------------------------------------------------------------

OBSERVATION-FIRST METHODOLOGY
The latency budgets and assertions below were derived from running
each scenario against the unfixed kernel and capturing the baseline:

- 2a: ``retrieve_memory`` with no ``user_id`` returns within a few
  milliseconds even when many writes for arbitrary user_ids are
  parked at the slow provider.  No barrier is consulted because
  the production path has none.
- 2b: ``retrieve_memory(user_id=U_r)`` returns immediately while
  ``create_memory(user_id=U_w)`` is parked, for any disjoint pair
  ``(U_r, U_w)``.
- 2c / 2g: serial ``add`` -> wait-for-commit -> ``retrieve`` returns
  the stored memory; the round-trip latency is dominated by the
  provider, not by any barrier wait.
- 2d / 2e: under ``InHouseProvider`` / ``ZepProvider``, the kernel
  retrieval path consults no pending-write registry and reaches the
  provider directly.  Stub providers that subclass the production
  classes verify the type-check identity is preserved.
- 2f: with ``auto_inject=False`` the ``ContextInjector`` short-
  circuits before any provider call - this is enforced by the
  existing early-return and is the contract the fix MUST keep.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from collections import OrderedDict
from typing import Any, Dict, List

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
from aios.memory.providers.in_house import InHouseProvider
from aios.memory.providers.zep import ZepProvider
from aios.memory.write_barrier import MemoryWriteBarrier
from aios.syscall.memory import MemorySyscall

from hypothesis import given, settings, strategies as st
from hypothesis import HealthCheck

from tests.modules.memory._doubles.open_access import (
    OpenAccessManager,
)
from tests.modules.memory._doubles.slow_mem0_provider import (
    SlowMem0Provider,
)


# ----------------------------------------------------------------------
# Tunable budgets
# ----------------------------------------------------------------------

# Maximum acceptable latency (seconds) for any retrieval that should
# bypass the barrier completely.  Generous enough to absorb CI jitter
# and process-level pauses; tight enough that a hidden barrier wait
# (or a real Mem0 round-trip) would blow through it.
FAST_PATH_BUDGET_S = 0.5


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------


def _make_manager(provider) -> MemoryManager:
    """Build a MemoryManager bound to a chosen provider without
    touching ConfigManager.

    ``MemoryManager.__init__`` reads the kernel-wide configuration
    and instantiates a real provider via ``ProviderFactory``; the
    preservation tests do not need that machinery, so we bypass
    ``__init__`` and wire the public attributes the production
    code actually reads.
    """
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    # ``MemoryManager.address_request`` releases the per-user write
    # barrier on every ``add_memory`` dispatch (task 5.3); install a
    # default barrier so the release call is a safe no-op on the
    # sentinel path. Tests that need an enabled barrier override this.
    manager.barrier = MemoryWriteBarrier(config={})
    manager.access_manager = OpenAccessManager()
    return manager


def _make_add_syscall(
    agent_name: str,
    user_id: str,
    content: str,
    sharing_policy: str = "shared",
    memory_type: str = "profile",
) -> MemorySyscall:
    return MemorySyscall(
        agent_name=agent_name,
        query=MemoryQuery(
            operation_type="add_memory",
            params={
                "content": content,
                "metadata": {
                    "user_id": user_id,
                    "owner_agent": agent_name,
                    "sharing_policy": sharing_policy,
                    "memory_type": memory_type,
                },
            },
        ),
    )


def _make_retrieve_syscall(
    agent_name: str,
    content: str,
    user_id: str | None = None,
) -> MemorySyscall:
    params: Dict[str, Any] = {"content": content, "k": 5}
    if user_id is not None:
        params["user_id"] = user_id
    return MemorySyscall(
        agent_name=agent_name,
        query=MemoryQuery(
            operation_type="retrieve_memory",
            params=params,
        ),
    )


def _start_writer(
    manager: MemoryManager,
    agent_name: str,
    user_id: str,
    content: str,
) -> threading.Thread:
    """Spawn a writer thread that issues add_memory through the
    real ``MemoryManager.address_request`` path."""
    syscall = _make_add_syscall(
        agent_name=agent_name,
        user_id=user_id,
        content=content,
    )

    def _run():
        manager.address_request(syscall)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


# ----------------------------------------------------------------------
# Stub providers for 2d / 2e
# ----------------------------------------------------------------------


class StubInHouseProvider(InHouseProvider):
    """Subclass of the production ``InHouseProvider`` that bypasses
    its backend wiring.

    Preserves ``isinstance(provider, InHouseProvider)`` identity so
    any production type-check in the fix path takes the InHouse
    code branch byte-for-byte.  Records every retrieval call so a
    test can assert that retrieval reached the provider directly,
    without consulting any pending-write registry.
    """

    def __init__(self) -> None:  # noqa: D401 - test double
        # Skip ``InHouseProvider.__init__`` so we don't allocate
        # vector-DB clients.
        self.retriever = None
        self.memories = {}
        self.add_calls: int = 0
        self.retrieve_calls: int = 0
        self.last_query_params: Dict[str, Any] | None = None

    def initialize(self, config: Dict[str, Any]) -> None:
        return None

    def add_memory(self, memory_note) -> MemoryResponse:
        self.add_calls += 1
        self.memories[memory_note.id] = memory_note
        return MemoryResponse(success=True, memory_id=memory_note.id)

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        self.memories.pop(memory_id, None)
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note) -> MemoryResponse:
        self.memories[memory_note.id] = memory_note
        return MemoryResponse(success=True, memory_id=memory_note.id)

    def get_memory(self, memory_id: str) -> MemoryResponse:
        note = self.memories.get(memory_id)
        if note is None:
            return MemoryResponse(success=False, error="not found")
        return MemoryResponse(
            success=True,
            content=note.content,
            metadata=dict(note.metadata or {}),
        )

    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        self.retrieve_calls += 1
        self.last_query_params = dict(query.params)
        return MemoryResponse(success=True, search_results=[])

    def retrieve_memory_raw(self, query: MemoryQuery) -> List:
        self.retrieve_calls += 1
        self.last_query_params = dict(query.params)
        return []

    def close(self) -> None:
        return None


class StubZepProvider(ZepProvider):
    """Subclass of the production ``ZepProvider`` that bypasses its
    Zep client wiring.  Same intent as ``StubInHouseProvider``."""

    def __init__(self) -> None:  # noqa: D401 - test double
        self.client = None
        self.default_user_id = "aios_default_user"
        self.default_session_id = "default"
        self.add_calls: int = 0
        self.retrieve_calls: int = 0
        self.last_query_params: Dict[str, Any] | None = None

    def initialize(self, config: Dict[str, Any]) -> None:
        return None

    def add_memory(self, memory_note) -> MemoryResponse:
        self.add_calls += 1
        return MemoryResponse(success=True, memory_id=memory_note.id)

    def remove_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_id)

    def update_memory(self, memory_note) -> MemoryResponse:
        return MemoryResponse(success=True, memory_id=memory_note.id)

    def get_memory(self, memory_id: str) -> MemoryResponse:
        return MemoryResponse(success=False, error="not found")

    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        self.retrieve_calls += 1
        self.last_query_params = dict(query.params)
        return MemoryResponse(success=True, search_results=[])

    def retrieve_memory_raw(self, query: MemoryQuery) -> List:
        self.retrieve_calls += 1
        self.last_query_params = dict(query.params)
        return []

    def close(self) -> None:
        return None


# ----------------------------------------------------------------------
# Hypothesis strategies
# ----------------------------------------------------------------------

# Small alphabet of user_ids: enough to surface user_id collisions but
# small enough that Hypothesis converges on minimal counterexamples
# quickly.
_USER_ALPHABET = st.sampled_from([
    "alex", "bob", "carol", "dave", "eve",
])

# Disjoint (read_uid, write_uid) pairs with read != write.
_DISJOINT_PAIRS = st.tuples(
    _USER_ALPHABET, _USER_ALPHABET,
).filter(lambda p: p[0] != p[1])


# ----------------------------------------------------------------------
# 2a - No-user_id Retrieval Preservation (Clause 3.3)
# ----------------------------------------------------------------------


class NoUserIdRetrievalPreservationTests(unittest.TestCase):
    """Retrievals issued with no ``user_id`` MUST take the existing
    fast path regardless of how many writes for arbitrary user_ids
    are in flight."""

    @given(
        write_uid=_USER_ALPHABET,
        num_pending=st.integers(min_value=0, max_value=4),
    )
    @settings(
        max_examples=8,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_no_user_id_retrieval_is_unaffected(
        self,
        write_uid: str,
        num_pending: int,
    ) -> None:
        """For every (write_uid, num_pending) pair, a retrieval
        without ``user_id`` returns within the fast-path budget
        and observes none of the still-parked writes."""
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        writers: List[threading.Thread] = []

        try:
            provider.park()
            for i in range(num_pending):
                writers.append(
                    _start_writer(
                        manager,
                        agent_name=f"WriterAgent{i}",
                        user_id=write_uid,
                        content=f"Pending fact #{i}",
                    ),
                )

            if num_pending:
                self.assertTrue(
                    provider.wait_until_pending(
                        num_pending, timeout=5.0,
                    ),
                    "Writers never reached the gate.",
                )

            retrieve_syscall = _make_retrieve_syscall(
                agent_name="ReaderAgent",
                content="anything",
                user_id=None,
            )

            t0 = time.perf_counter()
            response = manager.address_request(retrieve_syscall)
            elapsed = time.perf_counter() - t0

            self.assertTrue(response.success, msg=str(response))
            self.assertLessEqual(
                elapsed,
                FAST_PATH_BUDGET_S,
                (
                    f"Retrieval without user_id took {elapsed:.3f}s "
                    f"(budget {FAST_PATH_BUDGET_S:.3f}s) with "
                    f"{num_pending} pending writes for "
                    f"user_id={write_uid!r}.  Fast path was "
                    "violated."
                ),
            )
            # None of the parked writes have committed, so the
            # served snapshot is empty.
            self.assertEqual(
                len(response.search_results or []),
                0,
                (
                    "Retrieval without user_id MUST observe the "
                    "post-commit store snapshot only; got "
                    f"{len(response.search_results or [])} "
                    "results while writes were parked."
                ),
            )
        finally:
            provider.release()
            for thread in writers:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# 2b - Unrelated user_id Preservation (Clause 3.2)
# ----------------------------------------------------------------------


class UnrelatedUserIdPreservationTests(unittest.TestCase):
    """Retrievals for ``user_id=U_r`` MUST NOT be delayed by writes
    for any disjoint ``user_id=U_w``."""

    @given(
        pair=_DISJOINT_PAIRS,
        num_pending=st.integers(min_value=1, max_value=4),
    )
    @settings(
        max_examples=8,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_disjoint_user_id_retrieval_is_unaffected(
        self,
        pair: tuple,
        num_pending: int,
    ) -> None:
        read_uid, write_uid = pair
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        writers: List[threading.Thread] = []

        try:
            provider.park()
            for i in range(num_pending):
                writers.append(
                    _start_writer(
                        manager,
                        agent_name=f"WriterAgent{i}",
                        user_id=write_uid,
                        content=f"Fact #{i} about {write_uid}",
                    ),
                )

            self.assertTrue(
                provider.wait_until_pending(
                    num_pending, timeout=5.0,
                ),
                "Writers never reached the gate.",
            )

            retrieve_syscall = _make_retrieve_syscall(
                agent_name="ReaderAgent",
                content=f"anything about {read_uid}",
                user_id=read_uid,
            )

            t0 = time.perf_counter()
            response = manager.address_request(retrieve_syscall)
            elapsed = time.perf_counter() - t0

            self.assertTrue(response.success, msg=str(response))
            self.assertLessEqual(
                elapsed,
                FAST_PATH_BUDGET_S,
                (
                    f"Retrieval for user_id={read_uid!r} took "
                    f"{elapsed:.3f}s (budget "
                    f"{FAST_PATH_BUDGET_S:.3f}s) while "
                    f"{num_pending} writes for "
                    f"user_id={write_uid!r} were parked.  Fast "
                    "path was violated."
                ),
            )
            # Even on the fixed code, the retrieval for U_r
            # should never wait for U_w writes - so the served
            # snapshot still contains zero memories for U_r.
            self.assertEqual(
                len(response.search_results or []),
                0,
            )
        finally:
            provider.release()
            for thread in writers:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# 2c - Drained State Preservation (Clauses 3.1, 3.4, 3.6, 3.7)
# ----------------------------------------------------------------------


class DrainedStatePreservationTests(unittest.TestCase):
    """When all writes for ``user_id=U`` have already committed by
    the time the retrieval is issued, the retrieval MUST proceed at
    its existing latency profile and observe the committed
    memory."""

    @given(
        user_id=_USER_ALPHABET,
        num_writes=st.integers(min_value=1, max_value=4),
    )
    @settings(
        max_examples=6,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_serial_write_then_retrieve_is_unaffected(
        self,
        user_id: str,
        num_writes: int,
    ) -> None:
        provider = SlowMem0Provider()
        manager = _make_manager(provider)

        try:
            # Provider not parked: writes commit synchronously.
            for i in range(num_writes):
                add_syscall = _make_add_syscall(
                    agent_name="WriterAgent",
                    user_id=user_id,
                    content=f"Drained fact #{i} for {user_id}",
                )
                resp = manager.address_request(add_syscall)
                self.assertTrue(resp.success, msg=str(resp))

            # Sanity: store reflects all writes before retrieval.
            self.assertEqual(provider.store_size(), num_writes)
            self.assertEqual(provider.pending_count, 0)

            retrieve_syscall = _make_retrieve_syscall(
                agent_name="ReaderAgent",
                content=f"facts about {user_id}",
                user_id=user_id,
            )

            t0 = time.perf_counter()
            response = manager.address_request(retrieve_syscall)
            elapsed = time.perf_counter() - t0

            self.assertTrue(response.success, msg=str(response))
            self.assertLessEqual(
                elapsed,
                FAST_PATH_BUDGET_S,
                (
                    "Drained-state retrieval took "
                    f"{elapsed:.3f}s (budget "
                    f"{FAST_PATH_BUDGET_S:.3f}s)."
                ),
            )
            # All writes were shared; ReaderAgent sees them.
            results = response.search_results or []
            self.assertEqual(
                len(results),
                min(num_writes, 5),  # capped by k=5
            )
        finally:
            provider.release()
            provider.close()


# ----------------------------------------------------------------------
# 2d - InHouseProvider Preservation (Clause 3.5)
# ----------------------------------------------------------------------


class InHouseProviderPreservationTests(unittest.TestCase):
    """Under ``InHouseProvider``, the retrieval path MUST reach the
    provider directly without consulting any pending-write registry
    or barrier-related state.  This test stubs the provider type
    check by using a ``StubInHouseProvider`` that preserves the
    production class identity (``isinstance(p, InHouseProvider)``)
    while bypassing the real backend wiring."""

    def test_inhouse_retrieval_does_not_consult_barrier(self) -> None:
        provider = StubInHouseProvider()
        # Provider type identity is preserved.
        self.assertIsInstance(provider, InHouseProvider)

        manager = _make_manager(provider)

        # Issue a retrieval; the stub records the call but the
        # MemoryManager dispatch path makes no other calls
        # against the provider.  Once the fix lands, the
        # production type-check (``isinstance(provider,
        # Mem0Provider)``) MUST take the InHouse branch and
        # leave this assertion intact.
        retrieve_syscall = _make_retrieve_syscall(
            agent_name="ReaderAgent",
            content="anything",
            user_id="alex",
        )

        t0 = time.perf_counter()
        response = manager.address_request(retrieve_syscall)
        elapsed = time.perf_counter() - t0

        self.assertTrue(response.success, msg=str(response))
        self.assertEqual(provider.retrieve_calls, 1)
        self.assertEqual(provider.add_calls, 0)
        # agent_name is propagated through MemoryManager so
        # ``_apply_sharing_filter`` works inside the provider.
        self.assertEqual(
            provider.last_query_params.get("agent_name"),
            "ReaderAgent",
        )
        self.assertLessEqual(elapsed, FAST_PATH_BUDGET_S)


# ----------------------------------------------------------------------
# 2e - ZepProvider Preservation (Clause 3.5)
# ----------------------------------------------------------------------


class ZepProviderPreservationTests(unittest.TestCase):
    """Same shape as 2d, but for the ZepProvider type identity."""

    def test_zep_retrieval_does_not_consult_barrier(self) -> None:
        provider = StubZepProvider()
        self.assertIsInstance(provider, ZepProvider)

        manager = _make_manager(provider)

        retrieve_syscall = _make_retrieve_syscall(
            agent_name="ReaderAgent",
            content="anything",
            user_id="alex",
        )

        t0 = time.perf_counter()
        response = manager.address_request(retrieve_syscall)
        elapsed = time.perf_counter() - t0

        self.assertTrue(response.success, msg=str(response))
        self.assertEqual(provider.retrieve_calls, 1)
        self.assertEqual(provider.add_calls, 0)
        self.assertEqual(
            provider.last_query_params.get("agent_name"),
            "ReaderAgent",
        )
        self.assertLessEqual(elapsed, FAST_PATH_BUDGET_S)


# ----------------------------------------------------------------------
# 2f - auto_inject=false Preservation (Clause 3.5)
# ----------------------------------------------------------------------


class AutoInjectDisabledPreservationTests(unittest.TestCase):
    """When ``auto_inject`` is disabled, ``ContextInjector.inject``
    MUST short-circuit before any provider call.  No retrieval is
    issued, the query is returned unmodified, and no barrier is
    consulted."""

    def test_auto_inject_false_skips_retrieval(self) -> None:
        provider = SlowMem0Provider()
        manager = _make_manager(provider)

        injector = ContextInjector(
            memory_manager=manager,
            config={
                "auto_inject": False,
                "max_injected_memories": 5,
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        # Park the gate: any rogue add_memory issued by the
        # injector would block here and surface as a hang.
        provider.park()

        # Pre-stage: a writer is parked so that on a fixed kernel
        # with a barrier, a non-short-circuited inject() would
        # observably wait on it.  With auto_inject=False it never
        # gets that far.
        writer = _start_writer(
            manager,
            agent_name="WriterAgent",
            user_id="alex",
            content="Pending shared fact about alex.",
        )
        try:
            self.assertTrue(
                provider.wait_until_pending(1, timeout=5.0),
                "Writer never reached the gate.",
            )

            llm_query = LLMQuery(
                messages=[{
                    "role": "user",
                    "content": "What do you know about Alex?",
                }],
                action_type="chat",
            )
            original_messages = list(llm_query.messages)

            t0 = time.perf_counter()
            new_query, diagnostics = injector.inject(
                "AssistantAgent", llm_query,
            )
            elapsed = time.perf_counter() - t0

            self.assertLessEqual(
                elapsed,
                FAST_PATH_BUDGET_S,
                (
                    "ContextInjector with auto_inject=False "
                    f"took {elapsed:.3f}s; expected near-zero."
                ),
            )

            # Provider was not consulted at all.
            self.assertEqual(
                provider.retrieve_calls,
                0,
                (
                    "ContextInjector reached the provider with "
                    "auto_inject=False; this violates the "
                    "Clause 3.5 fast-path contract."
                ),
            )

            # Diagnostics reflect the disabled state.
            self.assertEqual(
                diagnostics.get("auto_inject_enabled"), False,
            )
            self.assertEqual(
                diagnostics.get("injected_count"), 0,
            )
            self.assertEqual(
                diagnostics.get("source_agents"), [],
            )
            self.assertEqual(
                diagnostics.get("memory_types"), [],
            )

            # Query messages are unchanged - no system message
            # was prepended.
            self.assertEqual(new_query.messages, original_messages)
        finally:
            provider.release()
            writer.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# 2g - Single-Agent Serial Preservation (Clause 3.6)
# ----------------------------------------------------------------------


class SingleAgentSerialPreservationTests(unittest.TestCase):
    """When a single agent issues ``create_memory`` and then its own
    ``retrieve_memory`` for the same ``user_id``, the retrieval MUST
    return the memory at the existing latency profile."""

    @given(
        user_id=_USER_ALPHABET,
        num_writes=st.integers(min_value=1, max_value=3),
    )
    @settings(
        max_examples=6,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_single_agent_serial_flow_is_unaffected(
        self,
        user_id: str,
        num_writes: int,
    ) -> None:
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        agent = "SoloAgent"

        try:
            # Sequential writes from the same agent.
            for i in range(num_writes):
                add_syscall = _make_add_syscall(
                    agent_name=agent,
                    user_id=user_id,
                    content=f"Solo fact #{i}",
                    sharing_policy="private",
                    memory_type="profile",
                )
                resp = manager.address_request(add_syscall)
                self.assertTrue(resp.success, msg=str(resp))

            # Same agent now retrieves.
            retrieve_syscall = _make_retrieve_syscall(
                agent_name=agent,
                content=f"solo facts for {user_id}",
                user_id=user_id,
            )

            t0 = time.perf_counter()
            response = manager.address_request(retrieve_syscall)
            elapsed = time.perf_counter() - t0

            self.assertTrue(response.success, msg=str(response))
            self.assertLessEqual(
                elapsed,
                FAST_PATH_BUDGET_S,
                (
                    "Single-agent serial retrieval took "
                    f"{elapsed:.3f}s (budget "
                    f"{FAST_PATH_BUDGET_S:.3f}s)."
                ),
            )
            # The agent sees its own private memories.
            results = response.search_results or []
            self.assertEqual(
                len(results),
                min(num_writes, 5),
            )
            # All returned memories are owned by the same agent.
            for mem in results:
                meta = mem.get("metadata") or {}
                self.assertEqual(
                    meta.get("owner_agent"), agent,
                )
        finally:
            provider.release()
            provider.close()


if __name__ == "__main__":
    unittest.main()
