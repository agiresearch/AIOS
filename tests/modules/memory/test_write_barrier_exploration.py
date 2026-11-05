"""
Bug condition exploration tests for the memory write-barrier.

These tests originally FAILED on the UNFIXED kernel - their failure
is what confirmed the bug exists.  Now that the kernel-level write
barrier is wired into ``MemoryManager`` (release on commit) and
``ContextInjector`` (inline waits before each retrieval), all three
cases PASS on the fixed code.

Case 1 was updated to stamp ``barrier_snapshot`` on the retrieve
syscall (replicating what ``SyscallExecutor`` does in production);
without this stamp the barrier wait short-circuits to BYPASSED.

Three exploration cases are encoded:

Case 1 (Explicit Retrieval Race) - PASSES post-fix
    A ``create_memory(user_id=alex)`` write is parked inside the
    slow provider gate.  A second agent issues
    ``retrieve_memory(user_id=alex)`` through
    ``manager.address_request`` with a ``barrier_snapshot`` stamp.
    The retrieval blocks until the write drains, then returns
    the committed memory.

Case 2 (Auto-Inject Race) - PASSES post-fix
    Two ``create_memory(user_id=alex, sharing_policy=shared)`` writes
    are parked.  ``AssistantAgent`` runs ``ContextInjector.inject``;
    the assertion encodes the post-fix expectation that both shared
    memories are reflected in the injection diagnostics
    (``injected_count == 2``, ``source_agents == [ProfileAgent,
    TaskAgent]``).  ``ContextInjector._await_pending_writes`` blocks
    until the writes drain.

Case 3 (Auto-Inject Multi-Writer) - PASSES post-fix
    A Hypothesis strategy varies ``(num_writes, jitter_ms)`` and
    asserts ``injected_count == num_writes`` after a delayed release.
    The cross-agent inline wait drains every parked write before the
    shared retrieval runs.

----------------------------------------------------------------------

OBSERVED COUNTEREXAMPLES ON UNFIXED CODE
(captured by running this test against the pre-fix kernel - see
.kiro/specs/memory-write-barrier/tasks.md task 1):

- Case 1: retrieve_memory(user_id=alex) returned 0 search_results
  while a single create_memory(user_id=alex) was parked at the
  slow provider gate.
    AssertionError: 0 != 1 : BUG: retrieve_memory(user_id=alex)
    returned 0 results while a create_memory(user_id=alex) was
    parked at the provider.  Expected 1 (write-before-read order).

- Case 2: ContextInjector.inject() returned
  diagnostics["injected_count"] == 0 and
  diagnostics["source_agents"] == [] while two parked shared
  writes for user_id=alex were in flight.
    AssertionError: 0 != 2 : BUG: ContextInjector saw
    injected_count=0 while two parked shared writes for
    user_id=alex were in flight.  Expected 2 (auto-inject wait
    for pending writes).

- Case 3: Hypothesis falsified the property at
  ``test_case3_auto_inject_multi_writer(num_writes=2,
  jitter_ms=0)``.
    AssertionError: 0 != 2 : BUG: injected_count=0 with
    num_writes=2, jitter_ms=0.  Expected 2 after barrier drain.

These observations confirm root cause analysis items 1-3 in
design.md ("Hypothesized Root Cause"): no pending-write registry,
no acceptance-time ordering hook, and direct provider calls from
ContextInjector that bypass any future syscall-level barrier.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unittest
from collections import OrderedDict

# Ensure project root on sys.path when invoked via pytest from any cwd.
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cerebrum.llm.apis import LLMQuery
from cerebrum.memory.apis import MemoryQuery

from aios.memory.context_injector import ContextInjector
from aios.memory.manager import MemoryManager
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
# Helpers
# ----------------------------------------------------------------------


def _make_manager(provider: SlowMem0Provider) -> MemoryManager:
    """Build a MemoryManager bound to the slow-provider double
    without touching ConfigManager.

    ``MemoryManager.__init__`` reads the kernel-wide configuration
    and instantiates a real provider via ``ProviderFactory``; the
    exploration tests do not need that machinery, so we bypass
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
    # sentinel path. The retrieval-side wait is not yet wired (task
    # 5.4), so these exploration tests continue to surface the bug.
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
    """Build a ``add_memory`` MemorySyscall for the given agent."""
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
    user_id: str,
    content: str,
) -> MemorySyscall:
    """Build a ``retrieve_memory`` MemorySyscall."""
    return MemorySyscall(
        agent_name=agent_name,
        query=MemoryQuery(
            operation_type="retrieve_memory",
            params={
                "content": content,
                "k": 5,
                "user_id": user_id,
            },
        ),
    )


def _start_writer(
    manager: MemoryManager,
    agent_name: str,
    user_id: str,
    content: str,
) -> threading.Thread:
    """Spawn a writer thread that issues add_memory through the
    real ``MemoryManager.address_request`` path.

    Mirrors the acceptance-time stamping that ``SyscallExecutor``
    performs on production syscalls (see
    ``aios/syscall/syscall.py``): before launching the writer
    thread we call ``manager.barrier.acquire(user_id)`` and stash
    the assigned ``seq_no`` on ``syscall.barrier_seq`` so that
    ``MemoryManager.address_request`` can drain it via
    ``barrier.release`` once the provider commit returns. Without
    this stamp the writer would never register a pending write
    against the barrier and ``ContextInjector._await_pending_writes``
    would short-circuit to ``BYPASSED``, hiding the very race the
    exploration tests are meant to surface.
    """
    syscall = _make_add_syscall(
        agent_name=agent_name,
        user_id=user_id,
        content=content,
    )
    # Stamp acceptance ordering exactly as SyscallExecutor would.
    syscall.barrier_seq = manager.barrier.acquire(user_id)

    def _run():
        manager.address_request(syscall)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


def _delayed_release(
    provider: SlowMem0Provider, delay_seconds: float,
) -> threading.Thread:
    """Schedule a release of the slow-provider gate after
    ``delay_seconds``.  Returns the scheduling thread so the test
    can join it during teardown."""

    def _run():
        time.sleep(delay_seconds)
        provider.release()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return thread


# ----------------------------------------------------------------------
# Cases 1 + 2 - deterministic single-shot exploration
# ----------------------------------------------------------------------


class WriteBarrierExplorationTests(unittest.TestCase):
    """Single-shot exploration of the explicit retrieval and
    auto-inject races."""

    def setUp(self) -> None:
        self.provider = SlowMem0Provider()
        self.manager = _make_manager(self.provider)
        self._writers: list[threading.Thread] = []

    def tearDown(self) -> None:
        # Always release the gate so any parked writers can
        # complete and the test process exits cleanly.
        self.provider.release()
        for thread in self._writers:
            thread.join(timeout=2.0)
        self.provider.close()

    # ------------------------------------------------------------------
    # Case 1: Explicit Retrieval Race
    # ------------------------------------------------------------------

    def test_case1_explicit_retrieval_race(self) -> None:
        """Agent A's create_memory(user_id=alex) is parked; Agent B
        issues retrieve_memory(user_id=alex).

        EXPECTED post-fix behaviour: the retrieval blocks until the
        write drains, then returns the committed memory.

        This test stamps ``barrier_snapshot`` on the retrieve syscall
        to replicate what ``SyscallExecutor`` does in production (it
        was previously omitted, which caused this test to always fail
        because the barrier wait short-circuited to BYPASSED).
        """
        # 1. Park the gate so add_memory blocks at the provider.
        self.provider.park()

        # 2. Spawn the writer for Agent A; it parks at the gate.
        self._writers.append(
            _start_writer(
                self.manager,
                agent_name="AgentA",
                user_id="alex",
                content="Alex prefers Python and dark roast coffee.",
            ),
        )

        # 3. Wait until the writer has registered at the gate so the
        # race is deterministic.
        self.assertTrue(
            self.provider.wait_until_pending(1, timeout=5.0),
            "Writer thread never reached the slow-provider gate.",
        )

        # 4. Schedule a release that will fire AFTER the retrieval
        # has had a chance to complete on UNFIXED code (which is
        # nearly instant) but BEFORE the fixed-code wait times out.
        self._writers.append(
            _delayed_release(self.provider, delay_seconds=0.15),
        )

        # 5. Issue the retrieval on Agent B.  Stamp barrier_snapshot
        # as SyscallExecutor would in production so the barrier wait
        # path is exercised.
        retrieve_syscall = _make_retrieve_syscall(
            agent_name="AgentB",
            user_id="alex",
            content="alex preferences",
        )
        retrieve_syscall.barrier_snapshot = (
            self.manager.barrier.snapshot("alex")
        )
        response = self.manager.address_request(retrieve_syscall)

        # 6. Assertion encodes the EXPECTED behaviour.
        self.assertTrue(response.success, msg=str(response))
        self.assertEqual(
            len(response.search_results or []),
            1,
            (
                "BUG: retrieve_memory(user_id=alex) returned "
                f"{len(response.search_results or [])} results while "
                "a create_memory(user_id=alex) was parked at the "
                "provider.  Expected 1 (write-before-read order)."
            ),
        )

    # ------------------------------------------------------------------
    # Case 2: Auto-Inject Race
    # ------------------------------------------------------------------

    def test_case2_auto_inject_race(self) -> None:
        """ProfileAgent + TaskAgent each park
        create_memory(user_id=alex, sharing_policy=shared);
        AssistantAgent runs ContextInjector.inject().

        EXPECTED post-fix behaviour:
            diagnostics["injected_count"] == 2
            sorted(diagnostics["source_agents"]) ==
                ["ProfileAgent", "TaskAgent"]

        UNFIXED behaviour: injected_count == 0 and source_agents
        == [] because the cross-agent retrieval inside the injector
        bypasses pending writes.
        """
        injector = ContextInjector(
            memory_manager=self.manager,
            config={
                "auto_inject": True,
                "max_injected_memories": 5,
                # Set threshold to 0 so SlowMem0Provider's score=0.9
                # passes the relevance gate cleanly.
                "relevance_threshold": 0.0,
                "max_memory_tokens": 8000,
            },
        )

        self.provider.park()

        self._writers.append(
            _start_writer(
                self.manager,
                agent_name="ProfileAgent",
                user_id="alex",
                content=(
                    "Alex's profile: senior engineer, "
                    "loves Python."
                ),
            ),
        )
        self._writers.append(
            _start_writer(
                self.manager,
                agent_name="TaskAgent",
                user_id="alex",
                content="Alex is preparing a Q1 roadmap.",
            ),
        )

        self.assertTrue(
            self.provider.wait_until_pending(2, timeout=5.0),
            "Writer threads never reached the slow-provider gate.",
        )

        self._writers.append(
            _delayed_release(self.provider, delay_seconds=0.15),
        )

        llm_query = LLMQuery(
            messages=[{
                "role": "user",
                "content": "What do you know about Alex?",
            }],
            action_type="chat",
        )

        _, diagnostics = injector.inject(
            "AssistantAgent", llm_query, user_id="alex"
        )

        self.assertEqual(
            diagnostics.get("injected_count"),
            2,
            (
                "BUG: ContextInjector saw "
                f"injected_count={diagnostics.get('injected_count')} "
                "while two parked shared writes for user_id=alex "
                "were in flight.  Expected 2 (auto-inject wait "
                "for pending writes)."
            ),
        )
        self.assertEqual(
            sorted(diagnostics.get("source_agents") or []),
            ["ProfileAgent", "TaskAgent"],
            (
                "BUG: source_agents="
                f"{diagnostics.get('source_agents')} - expected "
                "['ProfileAgent', 'TaskAgent'] after barrier drain."
            ),
        )


# ----------------------------------------------------------------------
# Case 3 - Hypothesis-driven multi-writer race
# ----------------------------------------------------------------------


class WriteBarrierMultiWriterRaceTests(unittest.TestCase):
    """Hypothesis-driven exploration of the auto-inject multi-writer
    race surface."""

    @given(
        num_writes=st.integers(min_value=2, max_value=4),
        jitter_ms=st.integers(min_value=0, max_value=50),
    )
    @settings(
        max_examples=5,
        deadline=None,
        suppress_health_check=[
            HealthCheck.function_scoped_fixture,
            HealthCheck.too_slow,
        ],
    )
    def test_case3_auto_inject_multi_writer(
        self,
        num_writes: int,
        jitter_ms: int,
    ) -> None:
        """For every ``(num_writes, jitter_ms)`` pair, parking
        ``num_writes`` shared writes for ``user_id=alex`` and then
        scheduling a release after ``jitter_ms`` should result in
        ``diagnostics["injected_count"] == num_writes`` once the
        write barrier is in place.

        On UNFIXED code Hypothesis reports the minimal
        counterexample (typically ``num_writes=2, jitter_ms=0``)
        because injection happens before the parked writes ever
        commit.
        """
        provider = SlowMem0Provider()
        manager = _make_manager(provider)
        writers: list[threading.Thread] = []

        try:
            injector = ContextInjector(
                memory_manager=manager,
                config={
                    "auto_inject": True,
                    "max_injected_memories": max(num_writes, 5),
                    "relevance_threshold": 0.0,
                    "max_memory_tokens": 8000,
                },
            )

            provider.park()

            for i in range(num_writes):
                writers.append(
                    _start_writer(
                        manager,
                        agent_name=f"WriterAgent{i}",
                        user_id="alex",
                        content=(
                            f"Fact #{i} about Alex: "
                            "loves Python."
                        ),
                    ),
                )

            self.assertTrue(
                provider.wait_until_pending(
                    num_writes, timeout=5.0,
                ),
                (
                    "Only "
                    f"{provider.pending_count}/"
                    f"{num_writes} writers reached the gate."
                ),
            )

            writers.append(
                _delayed_release(
                    provider,
                    delay_seconds=jitter_ms / 1000.0,
                ),
            )

            llm_query = LLMQuery(
                messages=[{
                    "role": "user",
                    "content": "Who is Alex?",
                }],
                action_type="chat",
            )

            _, diagnostics = injector.inject(
                "AssistantAgent", llm_query, user_id="alex",
            )

            self.assertEqual(
                diagnostics.get("injected_count"),
                num_writes,
                (
                    "BUG: injected_count="
                    f"{diagnostics.get('injected_count')} "
                    f"with num_writes={num_writes}, "
                    f"jitter_ms={jitter_ms}.  Expected "
                    f"{num_writes} after barrier drain."
                ),
            )
        finally:
            # Make sure no writer thread is left dangling between
            # Hypothesis examples - that would corrupt the next
            # example's pending-count synchronisation.
            provider.release()
            for thread in writers:
                thread.join(timeout=2.0)
            provider.close()


if __name__ == "__main__":
    unittest.main()
