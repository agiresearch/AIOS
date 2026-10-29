"""
Property-based tests for the integrated memory write barrier.

This suite uses Hypothesis to generate small interleaved schedules of
``create_memory`` and ``retrieve_memory`` operations over a fixed
alphabet of ``user_id`` values, then drives them through a real
``MemoryManager`` backed by ``SlowMem0Provider`` (the controllable
test double from task 1's _doubles directory). Six properties from
the design's "Property-Based Tests" section are encoded:

- Property 1 (Bug Condition / Fix Checking): every retrieval that
  satisfies ``isBugCondition`` (has user_id AND at least one
  accepted-but-uncommitted write for the same user_id) MUST observe
  every accepted-before-retrieval write for the same ``user_id``
  that ultimately committed. Validates Requirements 2.1, 2.2, 2.3.

- Property 2 (Preservation - Non-Bug Inputs Unchanged): for inputs
  where ``isBugCondition`` is false (drained schedules), the fixed
  kernel returns the same served result as a baseline kernel with
  the barrier disabled. Validates Requirements 3.1, 3.2, 3.3, 3.4,
  3.5, 3.6, 3.7.

- Property 3 (No Cross-User Blocking): retrievals scoped to
  ``user_id = U_a`` are not delayed by pending writes for
  ``user_id = U_b`` when ``U_a != U_b``. Validates Requirement 3.2.

- Property 4 (Bounded Wait): with ``timeout_ms = 100`` and a
  permanently-parked write, the retrieval returns within ~250 ms
  (CI buffer) and a TIMEOUT log event is recorded. Validates
  Requirements 2.1, 2.3.

- Property 5 (Failure Surfaces): when pending writes fail
  (``MemoryResponse(success=False)`` from the provider), retrievals
  waiting on those writes are released within timeout and the
  served snapshot is consistent with the writes that did commit.
  Validates Requirements 2.1, 2.3.

- Property 6 (Acceptance Ordering): retrievals only wait for writes
  whose ``seq_no <= retrieval.barrier_snapshot``; writes accepted
  *after* the retrieval's snapshot MUST NOT block it. Validates
  Requirements 2.2, 3.2.

Approach notes:

- ``MemoryManager`` is constructed via ``__new__`` + manual attribute
  wiring (mirroring the exploration tests) so the PBT does not need
  to spin up ``SyscallExecutor`` or ``ConfigManager``. This keeps
  every Hypothesis trial on the order of ~100 ms.
- Writer threads stamp ``barrier_seq`` manually (via
  ``manager.barrier.acquire(user_id)``) before kicking off the write
  through ``manager.address_request``, mirroring the acceptance-time
  stamping ``SyscallExecutor`` performs in production.
- Retrieval syscalls likewise stamp ``barrier_snapshot`` manually
  before dispatch so the manager's wait branch is exercised.
- Property 5 uses a ``FailingMem0Provider`` subclass that returns
  ``MemoryResponse(success=False)`` from ``add_memory`` (and exposes
  the same park / wait_until_pending helpers as ``SlowMem0Provider``)
  so failure paths are surfaced without breaking the gate-based
  synchronization the rest of the suite relies on.
"""
from __future__ import annotations

import logging
import os
import sys
import threading
import time
import unittest
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.memory.manager import MemoryManager
from aios.memory.write_barrier import MemoryWriteBarrier, WaitOutcome
from aios.syscall.memory import MemorySyscall

from hypothesis import HealthCheck, given, settings, strategies as st

from tests.modules.memory._doubles.open_access import (
    OpenAccessManager,
)
from tests.modules.memory._doubles.slow_mem0_provider import (
    SlowMem0Provider,
)


# ----------------------------------------------------------------------
# Constants and strategies
# ----------------------------------------------------------------------

# Small alphabet of user_ids: large enough to surface user_id collisions
# but small enough that Hypothesis converges on minimal counterexamples
# quickly. Matches the exploration / preservation suites.
USER_IDS = ["alex", "bob", "carol"]

_USER_STRATEGY = st.sampled_from(USER_IDS)


# ----------------------------------------------------------------------
# Test doubles
# ----------------------------------------------------------------------


class FailingMem0Provider(SlowMem0Provider):
    """Variant of ``SlowMem0Provider`` that decides per-write whether
    the commit succeeds or fails based on the ``_test_fail`` flag in
    each note's metadata.

    Property 5 needs writes that *fail* without raising, while still
    going through the same gate / pending-count synchronization the
    rest of the suite uses. We can't use a single provider-wide
    "fail" flag because the test mixes failing and successful writes
    that all park on the same gate and release together; toggling a
    boolean between staging stages races with the gated writers.

    The metadata-based flag pins the decision to each individual
    write at thread-spawn time, eliminating that race.
    """

    def add_memory(self, memory_note) -> MemoryResponse:  # type: ignore[override]
        # Mirror the parent's gate / pending-count logic so
        # ``wait_until_pending`` works the same way; only the commit
        # path changes.
        with self._pending_lock:
            self._pending_count += 1
            self.add_calls += 1
            self._pending_cv.notify_all()
        try:
            self._gate.wait()
        finally:
            with self._pending_lock:
                self._pending_count -= 1
                self._pending_cv.notify_all()

        should_fail = bool(
            (memory_note.metadata or {}).get("_test_fail", False)
        )
        if should_fail:
            # Failing writes must NOT land in the committed store —
            # that is what makes them observably failed to a
            # subsequent retrieval.
            return MemoryResponse(
                success=False,
                error="FailingMem0Provider: simulated write failure",
            )

        # Successful path: append to the committed store with the
        # same shape the parent class uses so retrieval results match.
        with self._store_lock:
            self._store.append({
                "memory_id": memory_note.id,
                "content": memory_note.content,
                "metadata": dict(memory_note.metadata or {}),
                "timestamp": memory_note.timestamp,
                "keywords": list(memory_note.keywords or []),
                "tags": list(memory_note.tags or []),
                "category": memory_note.category or "Uncategorized",
            })
        return MemoryResponse(success=True, memory_id=memory_note.id)


# ----------------------------------------------------------------------
# Manager / syscall helpers
# ----------------------------------------------------------------------


def _make_manager(
    provider: SlowMem0Provider,
    barrier_config: Optional[Dict[str, Any]] = None,
) -> MemoryManager:
    """Build a MemoryManager bound to *provider* without touching
    ConfigManager. Mirrors the helper used by the exploration and
    preservation suites so the PBT trial cost stays low.
    """
    manager = MemoryManager.__new__(MemoryManager)
    manager.log_mode = "console"
    manager._known_user_ids = OrderedDict()
    manager.provider = provider
    manager.barrier = MemoryWriteBarrier(config=barrier_config or {})
    # Writers and readers are different agents; access
    # control is not under test here.
    manager.access_manager = OpenAccessManager()
    return manager


def _make_add_syscall(
    agent_name: str, user_id: str, content: str,
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
                    "sharing_policy": "shared",
                    "memory_type": "profile",
                },
            },
        ),
    )


def _make_retrieve_syscall(
    agent_name: str, user_id: str, content: str,
) -> MemorySyscall:
    return MemorySyscall(
        agent_name=agent_name,
        query=MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": content,
                "k": 10,
                "user_id": user_id,
            },
        ),
    )


def _start_writer(
    manager: MemoryManager,
    agent_name: str,
    user_id: str,
    content: str,
) -> Tuple[threading.Thread, int]:
    """Spawn a writer thread that issues ``add_memory`` through
    ``manager.address_request``.

    Manually stamps ``syscall.barrier_seq`` via
    ``manager.barrier.acquire(user_id)`` *before* the thread starts so
    the barrier registry contains the pending entry before any
    retrieval can take a snapshot. Returns the thread plus the
    assigned ``seq_no`` so the caller can reason about acceptance
    ordering.
    """
    syscall = _make_add_syscall(agent_name, user_id, content)
    seq_no = manager.barrier.acquire(user_id)
    syscall.barrier_seq = seq_no

    def _run() -> None:
        manager.address_request(syscall)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread, seq_no


def _retrieve_with_snapshot(
    manager: MemoryManager,
    agent_name: str,
    user_id: str,
    content: str = "query",
    deadline_seconds: Optional[float] = None,
) -> Tuple[MemoryResponse, int, float]:
    """Issue ``retrieve_memory`` through the manager with manually
    stamped ``barrier_snapshot``.

    Returns ``(response, snapshot, elapsed_seconds)`` so callers can
    correlate latency, the snapshot the retrieval waited on, and the
    served result in a single tuple.
    """
    syscall = _make_retrieve_syscall(agent_name, user_id, content)
    snapshot = manager.barrier.snapshot(user_id)
    syscall.barrier_snapshot = snapshot

    if deadline_seconds is not None:
        # When a custom deadline is supplied (Property 4), monkey-patch
        # the manager's wait call so the PBT can surface the bounded
        # wait without changing the production code path. Wrapping
        # rather than mutating barrier state keeps the trial isolated.
        original_wait = manager.barrier.wait_until_drained

        def _wait_with_deadline(uid, seq):
            return original_wait(uid, seq, deadline=deadline_seconds)

        manager.barrier.wait_until_drained = _wait_with_deadline  # type: ignore[assignment]
        try:
            t0 = time.perf_counter()
            response = manager.address_request(syscall)
            elapsed = time.perf_counter() - t0
        finally:
            manager.barrier.wait_until_drained = original_wait  # type: ignore[assignment]
    else:
        t0 = time.perf_counter()
        response = manager.address_request(syscall)
        elapsed = time.perf_counter() - t0

    return response, snapshot, elapsed


# ----------------------------------------------------------------------
# Property 1: Bug Condition / Fix Checking
# ----------------------------------------------------------------------


class Property1BugConditionTests(unittest.TestCase):
    """Every retrieval that satisfies ``isBugCondition`` MUST observe
    every accepted-before-retrieval write for the same ``user_id``
    that ultimately committed.
    """

    @given(
        target_user=_USER_STRATEGY,
        num_writes=st.integers(min_value=1, max_value=4),
        # Writes for *other* user_ids parked in flight to surface
        # cross-user noise without changing the property under test.
        num_other_writes=st.integers(min_value=0, max_value=2),
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_retrieval_observes_all_accepted_writes(
        self,
        target_user: str,
        num_writes: int,
        num_other_writes: int,
    ) -> None:
        """**Validates: Requirements 2.1, 2.2, 2.3**"""
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        threads: List[threading.Thread] = []

        try:
            provider.park()

            # Park ``num_writes`` writes for the target user.
            for i in range(num_writes):
                thread, _ = _start_writer(
                    manager,
                    agent_name=f"WriterAgent{i}",
                    user_id=target_user,
                    content=f"target fact #{i} for {target_user}",
                )
                threads.append(thread)

            # Park ``num_other_writes`` writes for a different user
            # (cycle through the alphabet skipping ``target_user``).
            other_users = [u for u in USER_IDS if u != target_user]
            for j in range(num_other_writes):
                other = other_users[j % len(other_users)]
                thread, _ = _start_writer(
                    manager,
                    agent_name=f"OtherAgent{j}",
                    user_id=other,
                    content=f"unrelated fact #{j} for {other}",
                )
                threads.append(thread)

            # Wait until every writer is parked at the gate so the
            # bug condition is deterministic.
            total_pending = num_writes + num_other_writes
            self.assertTrue(
                provider.wait_until_pending(
                    total_pending, timeout=5.0,
                ),
                "Writers never reached the gate.",
            )

            # Schedule the gate release after the retrieval has had a
            # chance to park on the barrier. 100 ms is far below the
            # default 5 s barrier timeout but well above the
            # near-instant unfixed retrieval path.
            release_thread = threading.Thread(
                target=lambda: (time.sleep(0.1), provider.release()),
                daemon=True,
            )
            release_thread.start()
            threads.append(release_thread)

            # Issue the retrieval. The barrier MUST hold it until
            # every parked write for ``target_user`` drains.
            response, snapshot, _ = _retrieve_with_snapshot(
                manager,
                agent_name="ReaderAgent",
                user_id=target_user,
                content=f"facts about {target_user}",
            )

            # All target writes must have committed by the time the
            # response is materialized — the served snapshot must
            # contain exactly ``num_writes`` memories for the user.
            self.assertTrue(response.success, msg=str(response))
            results = response.search_results or []
            target_results = [
                r for r in results
                if (r.get("metadata") or {}).get(
                    "user_id"
                ) == target_user
            ]
            self.assertEqual(
                len(target_results),
                num_writes,
                (
                    f"Property 1 violated: served {len(target_results)} "
                    f"memories for user_id={target_user!r} after "
                    f"{num_writes} accepted writes drained "
                    f"(snapshot={snapshot})."
                ),
            )
            # The barrier registry must be empty for the target user
            # by the time the retrieval returns.
            stats = manager.barrier.stats()
            self.assertNotIn(
                target_user,
                stats["pending_by_user"],
                (
                    "Pending writes for target user remain after a "
                    "successful retrieval; barrier did not drain "
                    "fully."
                ),
            )
        finally:
            provider.release()
            for thread in threads:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# Property 2: Preservation - Non-Bug Inputs Unchanged
# ----------------------------------------------------------------------


class Property2PreservationTests(unittest.TestCase):
    """For schedules where ``isBugCondition`` is false (every write
    has committed before the retrieval is accepted), the fixed
    kernel MUST produce the same served result as a baseline kernel
    with the barrier disabled.
    """

    @given(
        target_user=_USER_STRATEGY,
        num_writes=st.integers(min_value=1, max_value=4),
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_drained_schedule_matches_baseline(
        self,
        target_user: str,
        num_writes: int,
    ) -> None:
        """**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6,
        3.7**
        """
        # Baseline: barrier disabled. Provider not parked, writes
        # commit synchronously, retrieval served from the post-commit
        # snapshot.
        baseline_provider = SlowMem0Provider()
        baseline_manager = _make_manager(
            baseline_provider, barrier_config={"enabled": False},
        )
        # Fixed kernel: barrier enabled. Same drained-schedule input.
        fixed_provider = SlowMem0Provider()
        fixed_manager = _make_manager(
            fixed_provider, barrier_config={"enabled": True},
        )

        try:
            for i in range(num_writes):
                content = f"drained fact #{i} for {target_user}"
                # Baseline write — synchronous, no barrier stamping
                # because barrier is disabled.
                baseline_syscall = _make_add_syscall(
                    f"WriterAgent{i}", target_user, content,
                )
                baseline_resp = baseline_manager.address_request(
                    baseline_syscall,
                )
                self.assertTrue(
                    baseline_resp.success, msg=str(baseline_resp),
                )

                # Fixed write — synchronous via the same code path.
                fixed_syscall = _make_add_syscall(
                    f"WriterAgent{i}", target_user, content,
                )
                fixed_syscall.barrier_seq = (
                    fixed_manager.barrier.acquire(target_user)
                )
                fixed_resp = fixed_manager.address_request(
                    fixed_syscall,
                )
                self.assertTrue(
                    fixed_resp.success, msg=str(fixed_resp),
                )

            # Sanity: the schedule is drained — no pending writes.
            self.assertEqual(baseline_provider.pending_count, 0)
            self.assertEqual(fixed_provider.pending_count, 0)
            self.assertEqual(
                fixed_manager.barrier.stats()["total_pending"], 0,
            )

            # Run identical retrievals against both kernels.
            baseline_resp, _, _ = _retrieve_with_snapshot(
                baseline_manager,
                agent_name="ReaderAgent",
                user_id=target_user,
                content=f"facts about {target_user}",
            )
            fixed_resp, _, _ = _retrieve_with_snapshot(
                fixed_manager,
                agent_name="ReaderAgent",
                user_id=target_user,
                content=f"facts about {target_user}",
            )

            self.assertTrue(
                baseline_resp.success, msg=str(baseline_resp),
            )
            self.assertTrue(fixed_resp.success, msg=str(fixed_resp))

            # Compare the served snapshots: the contents (not the
            # ordering, which can vary by stable-sort tie-breaks) must
            # match exactly.
            baseline_contents = sorted(
                (r.get("content") or "")
                for r in (baseline_resp.search_results or [])
            )
            fixed_contents = sorted(
                (r.get("content") or "")
                for r in (fixed_resp.search_results or [])
            )
            self.assertEqual(
                baseline_contents,
                fixed_contents,
                (
                    "Property 2 violated: drained-schedule retrieval "
                    "diverged between barrier-disabled and "
                    "barrier-enabled kernels."
                ),
            )
        finally:
            baseline_provider.release()
            baseline_provider.close()
            fixed_provider.release()
            fixed_provider.close()


# ----------------------------------------------------------------------
# Property 3: No Cross-User Blocking
# ----------------------------------------------------------------------


class Property3NoCrossUserBlockingTests(unittest.TestCase):
    """Retrievals scoped to ``user_id = U_a`` MUST NOT be delayed by
    pending writes for ``user_id = U_b`` when ``U_a != U_b``.
    """

    @given(
        pair=st.tuples(_USER_STRATEGY, _USER_STRATEGY).filter(
            lambda p: p[0] != p[1],
        ),
        num_pending=st.integers(min_value=1, max_value=4),
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_disjoint_user_retrieval_is_not_delayed(
        self,
        pair: Tuple[str, str],
        num_pending: int,
    ) -> None:
        """**Validates: Requirement 3.2**"""
        read_uid, write_uid = pair
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        threads: List[threading.Thread] = []

        try:
            provider.park()
            for i in range(num_pending):
                thread, _ = _start_writer(
                    manager,
                    agent_name=f"WriterAgent{i}",
                    user_id=write_uid,
                    content=f"fact #{i} for {write_uid}",
                )
                threads.append(thread)

            self.assertTrue(
                provider.wait_until_pending(
                    num_pending, timeout=5.0,
                ),
                "Writers never reached the gate.",
            )

            # Sanity: pending entries belong to ``write_uid`` only.
            stats = manager.barrier.stats()
            self.assertEqual(
                stats["pending_by_user"].get(write_uid),
                num_pending,
            )
            self.assertNotIn(
                read_uid, stats["pending_by_user"],
            )

            response, _, elapsed = _retrieve_with_snapshot(
                manager,
                agent_name="ReaderAgent",
                user_id=read_uid,
                content=f"anything about {read_uid}",
            )

            self.assertTrue(response.success, msg=str(response))
            # The retrieval MUST NOT have waited on the U_b writes.
            # 50 ms is comfortable headroom over the no-op fast path
            # while still being tight enough to catch a regression
            # that parks the disjoint-user waiter on U_b's pending
            # writes.
            self.assertLess(
                elapsed,
                0.05,
                (
                    f"Property 3 violated: retrieval for "
                    f"user_id={read_uid!r} took {elapsed:.4f}s while "
                    f"{num_pending} writes for "
                    f"user_id={write_uid!r} were parked. "
                    "Expected <50 ms."
                ),
            )
            # The pending writes for ``write_uid`` are still parked —
            # the disjoint-user wait must not have side-drained them.
            stats_after = manager.barrier.stats()
            self.assertEqual(
                stats_after["pending_by_user"].get(write_uid),
                num_pending,
            )
        finally:
            provider.release()
            for thread in threads:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# Property 4: Bounded Wait
# ----------------------------------------------------------------------


class Property4BoundedWaitTests(unittest.TestCase):
    """With ``timeout_ms = 100`` and a permanently parked write, the
    retrieval MUST return within ~250 ms (CI buffer) and a TIMEOUT
    log event MUST be recorded.
    """

    @given(
        target_user=_USER_STRATEGY,
        num_pending=st.integers(min_value=1, max_value=3),
    )
    @settings(
        max_examples=8,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_bounded_wait_with_parked_write(
        self,
        target_user: str,
        num_pending: int,
    ) -> None:
        """**Validates: Requirements 2.1, 2.3**"""
        provider = SlowMem0Provider()
        # Configure the barrier with a 100 ms timeout to surface
        # bounded-wait behavior quickly.
        manager = _make_manager(
            provider, barrier_config={"timeout_ms": 100},
        )
        threads: List[threading.Thread] = []

        try:
            provider.park()
            for i in range(num_pending):
                thread, _ = _start_writer(
                    manager,
                    agent_name=f"WriterAgent{i}",
                    user_id=target_user,
                    content=f"parked fact #{i} for {target_user}",
                )
                threads.append(thread)

            self.assertTrue(
                provider.wait_until_pending(
                    num_pending, timeout=5.0,
                ),
                "Writers never reached the gate.",
            )

            # NOTE: provider is *never* released during the retrieval,
            # so the barrier MUST hit its 100 ms deadline and TIMEOUT.
            with self.assertLogs(
                "aios.memory.write_barrier", level=logging.WARNING,
            ) as captured:
                response, _, elapsed = _retrieve_with_snapshot(
                    manager,
                    agent_name="ReaderAgent",
                    user_id=target_user,
                    content=f"anything about {target_user}",
                )

            # Retrieval must return within the configured bound + CI
            # buffer (250 ms is the design's recommended ceiling).
            self.assertLess(
                elapsed,
                0.25,
                (
                    f"Property 4 violated: retrieval took "
                    f"{elapsed:.3f}s with timeout_ms=100. "
                    "Expected <250 ms."
                ),
            )
            self.assertTrue(response.success, msg=str(response))

            # A TIMEOUT WARNING must be recorded so operators can
            # correlate stuck writes with retrieval latency.
            warning_messages = "\n".join(
                r.getMessage() for r in captured.records
                if r.levelno == logging.WARNING
            )
            self.assertIn("TIMEOUT", warning_messages)
            self.assertIn(repr(target_user), warning_messages)
        finally:
            provider.release()
            for thread in threads:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# Property 5: Failure Surfaces
# ----------------------------------------------------------------------


class Property5FailureSurfacesTests(unittest.TestCase):
    """When pending writes fail (``MemoryResponse(success=False)``),
    retrievals waiting on those writes MUST be released within
    timeout and the served snapshot MUST be consistent with the
    writes that did commit.
    """

    @given(
        target_user=_USER_STRATEGY,
        num_failing_writes=st.integers(min_value=1, max_value=3),
        num_successful_writes=st.integers(min_value=0, max_value=2),
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_failed_writes_release_waiters(
        self,
        target_user: str,
        num_failing_writes: int,
        num_successful_writes: int,
    ) -> None:
        """**Validates: Requirements 2.1, 2.3**"""
        provider = FailingMem0Provider()
        manager = _make_manager(
            provider, barrier_config={"timeout_ms": 5000},
        )
        threads: List[threading.Thread] = []

        def _start_failing_writer(
            agent_name: str, content: str, will_fail: bool,
        ) -> threading.Thread:
            """Spawn a writer whose metadata carries ``_test_fail`` so
            the per-write fail decision is fixed at thread-spawn
            time. This avoids races between toggling a provider-wide
            boolean and the gated writers."""
            syscall = MemorySyscall(
                agent_name=agent_name,
                query=MemoryQuery(
                    operation_type="add_memory",
                    params={
                        "content": content,
                        "metadata": {
                            "user_id": target_user,
                            "owner_agent": agent_name,
                            "sharing_policy": "shared",
                            "memory_type": "profile",
                            "_test_fail": will_fail,
                        },
                    },
                ),
            )
            syscall.barrier_seq = manager.barrier.acquire(target_user)

            def _run() -> None:
                manager.address_request(syscall)

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()
            return thread

        try:
            provider.park()

            # Mix failing + successful writers — all park together,
            # all release together. Per-write metadata pins the
            # success/failure decision so the trial is deterministic.
            for i in range(num_failing_writes):
                threads.append(
                    _start_failing_writer(
                        f"FailAgent{i}",
                        f"failing fact #{i}",
                        will_fail=True,
                    )
                )
            for j in range(num_successful_writes):
                threads.append(
                    _start_failing_writer(
                        f"OkAgent{j}",
                        f"committed fact #{j}",
                        will_fail=False,
                    )
                )

            total = num_failing_writes + num_successful_writes
            self.assertTrue(
                provider.wait_until_pending(total, timeout=5.0),
                "Writers never reached the gate.",
            )

            # Schedule the release so all parked writers (failing +
            # successful) drain. Failed writes must still release
            # barrier waiters per ``write_barrier.release`` semantics.
            release_thread = threading.Thread(
                target=lambda: (time.sleep(0.05), provider.release()),
                daemon=True,
            )
            release_thread.start()
            threads.append(release_thread)

            response, _, elapsed = _retrieve_with_snapshot(
                manager,
                agent_name="ReaderAgent",
                user_id=target_user,
                content=f"facts about {target_user}",
            )

            # Retrieval must complete within the configured timeout.
            # Failed writes must drain the barrier so the retrieval
            # is released, not stranded.
            self.assertLess(
                elapsed,
                5.0,
                (
                    f"Property 5 violated: retrieval took "
                    f"{elapsed:.3f}s while failing writes were in "
                    "flight. Failed writes must release waiters."
                ),
            )
            self.assertTrue(response.success, msg=str(response))

            # The served snapshot must match the writes that did
            # commit (i.e., ``num_successful_writes``). Failing
            # writes must NOT show up in the result.
            results = response.search_results or []
            target_results = [
                r for r in results
                if (r.get("metadata") or {}).get(
                    "user_id"
                ) == target_user
            ]
            self.assertEqual(
                len(target_results),
                num_successful_writes,
                (
                    f"Property 5 violated: served "
                    f"{len(target_results)} memories for "
                    f"user_id={target_user!r}, expected "
                    f"{num_successful_writes} (failing writes must "
                    "not be visible)."
                ),
            )

            # Barrier must be fully drained for the target user.
            stats = manager.barrier.stats()
            self.assertNotIn(
                target_user, stats["pending_by_user"],
            )
        finally:
            provider.release()
            for thread in threads:
                thread.join(timeout=2.0)
            provider.close()


# ----------------------------------------------------------------------
# Property 6: Acceptance Ordering
# ----------------------------------------------------------------------


class Property6AcceptanceOrderingTests(unittest.TestCase):
    """Retrievals MUST only wait for writes whose
    ``seq_no <= retrieval.barrier_snapshot``. Writes accepted *after*
    the retrieval's snapshot MUST NOT block it.
    """

    @given(
        target_user=_USER_STRATEGY,
        num_pre_snapshot_writes=st.integers(min_value=0, max_value=3),
        num_post_snapshot_writes=st.integers(min_value=1, max_value=3),
    )
    @settings(
        max_examples=10,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_retrieval_does_not_wait_on_post_snapshot_writes(
        self,
        target_user: str,
        num_pre_snapshot_writes: int,
        num_post_snapshot_writes: int,
    ) -> None:
        """**Validates: Requirements 2.2, 3.2**"""
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        threads: List[threading.Thread] = []

        try:
            # Stage 1: park ``num_pre_snapshot_writes`` writes — these
            # will be drained before the retrieval is taken so the
            # snapshot is not blocked by them.
            if num_pre_snapshot_writes > 0:
                provider.park()
                for i in range(num_pre_snapshot_writes):
                    thread, _ = _start_writer(
                        manager,
                        agent_name=f"PreAgent{i}",
                        user_id=target_user,
                        content=f"pre fact #{i}",
                    )
                    threads.append(thread)

                self.assertTrue(
                    provider.wait_until_pending(
                        num_pre_snapshot_writes, timeout=5.0,
                    ),
                    "Pre-snapshot writers never reached the gate.",
                )
                provider.release()
                for thread in threads:
                    thread.join(timeout=2.0)
                # Confirm pre-snapshot writes drained.
                self.assertEqual(
                    manager.barrier.stats()["total_pending"], 0,
                )
                threads = []

            # Stage 2: take the retrieval's snapshot NOW — it captures
            # the high-water mark *before* the post-snapshot writes
            # are accepted.
            snapshot_before_late_writes = (
                manager.barrier.snapshot(target_user)
            )

            # Stage 3: park ``num_post_snapshot_writes`` writes that
            # arrive *after* the snapshot. Their seq_nos will be
            # strictly greater than ``snapshot_before_late_writes``,
            # so a correct barrier MUST NOT block on them.
            provider.park()
            late_seq_nos: List[int] = []
            for j in range(num_post_snapshot_writes):
                thread, seq = _start_writer(
                    manager,
                    agent_name=f"LateAgent{j}",
                    user_id=target_user,
                    content=f"late fact #{j}",
                )
                threads.append(thread)
                late_seq_nos.append(seq)

            self.assertTrue(
                provider.wait_until_pending(
                    num_post_snapshot_writes, timeout=5.0,
                ),
                "Late writers never reached the gate.",
            )

            # Sanity: every late seq_no is strictly greater than the
            # captured snapshot — otherwise the test setup is broken.
            for late_seq in late_seq_nos:
                self.assertGreater(
                    late_seq,
                    snapshot_before_late_writes,
                    (
                        "Test setup error: late seq_no "
                        f"{late_seq} not strictly greater than "
                        f"snapshot {snapshot_before_late_writes}."
                    ),
                )

            # Stage 4: dispatch the retrieval against the captured
            # snapshot. Even though late writes are parked, the
            # retrieval MUST proceed immediately because no pending
            # write satisfies ``seq_no <= snapshot``.
            syscall = _make_retrieve_syscall(
                "ReaderAgent", target_user, content="late check",
            )
            syscall.barrier_snapshot = snapshot_before_late_writes

            t0 = time.perf_counter()
            response = manager.address_request(syscall)
            elapsed = time.perf_counter() - t0

            self.assertTrue(response.success, msg=str(response))
            # 50 ms is comfortable headroom over the no-op fast path
            # while still being tight enough to catch a regression
            # that parks the snapshot-ordered waiter on later writes.
            self.assertLess(
                elapsed,
                0.05,
                (
                    f"Property 6 violated: retrieval with "
                    f"snapshot={snapshot_before_late_writes} took "
                    f"{elapsed:.4f}s while later seq_nos "
                    f"{late_seq_nos} were parked. Expected <50 ms "
                    "(retrieval must not wait on post-snapshot "
                    "writes)."
                ),
            )

            # Late writes are still parked — the snapshot-ordered
            # wait must not have side-drained them.
            stats = manager.barrier.stats()
            self.assertEqual(
                stats["pending_by_user"].get(target_user),
                num_post_snapshot_writes,
            )
        finally:
            provider.release()
            for thread in threads:
                thread.join(timeout=2.0)
            provider.close()


if __name__ == "__main__":
    unittest.main()
