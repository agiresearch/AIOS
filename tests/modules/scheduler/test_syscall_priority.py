"""A client's requested priority must reach the syscall the scheduler reads.

Two halves of that path exist:

1. ``runtime/launch.py`` attaches the priority from ``POST /query`` onto the
   query object as a private attribute -- the same mechanism it already uses
   for ``user_id`` -- so the Cerebrum SDK query types stay unmodified.
2. ``SyscallExecutor`` reads that attribute back and stamps it onto the syscall
   it creates, which is what ``PriorityScheduler`` then reads via
   ``syscall.get_priority()``.

This module verifies half two, which is the half that runs inside the kernel.
It does so without starting a server or a model backend by replacing the LLM
request queue with a capture that completes the syscall the way the real
adapter would.
"""

from __future__ import annotations

from typing import Any, Callable, List

import pytest

pytest.importorskip("cerebrum")

from cerebrum.llm.apis import LLMQuery  # noqa: E402

import aios.syscall.syscall as syscall_module  # noqa: E402
from aios.scheduler.priority_policy import (  # noqa: E402
    PendingRequest,
    PriorityLevel,
    PriorityPolicy,
)
from aios.syscall.syscall import SyscallExecutor  # noqa: E402


@pytest.fixture
def captured_syscalls(monkeypatch) -> List[Any]:
    """Capture LLM syscalls instead of queueing them for a real scheduler.

    The replacement also completes each syscall (response, ``done`` status and
    the event) so ``_execute_syscall`` returns rather than blocking forever on
    ``syscall.join()``.
    """
    captured: List[Any] = []

    def enqueue(syscall: Any) -> None:
        captured.append(syscall)
        syscall.set_response("ok")
        syscall.set_status("done")
        syscall.set_end_time(0.0)
        syscall.event.set()

    monkeypatch.setattr(
        syscall_module, "global_llm_req_queue_add_message", enqueue
    )
    return captured


def _chat_query() -> LLMQuery:
    """Return a minimal chat query, as the kernel handler builds it."""
    return LLMQuery(
        messages=[{"role": "user", "content": "hello"}],
        action_type="chat",
    )


def test_requested_priority_is_stamped_on_the_syscall(captured_syscalls):
    query = _chat_query()
    query._request_priority = "high"

    SyscallExecutor().execute_llm_syscall("agent_A", query)

    assert captured_syscalls[0].get_priority() == "high"


def test_integer_priority_is_accepted(captured_syscalls):
    """The endpoint documents both a name and a level (0 = high, 2 = low)."""
    query = _chat_query()
    query._request_priority = 0

    SyscallExecutor().execute_llm_syscall("agent_A", query)

    assert captured_syscalls[0].get_priority() == 0


def test_absent_priority_leaves_the_syscall_untouched(captured_syscalls):
    """A request that sends no priority keeps the syscall's default of None.

    This is what keeps the change inert for every existing client and for the
    FIFO and round-robin policies.
    """
    SyscallExecutor().execute_llm_syscall("agent_A", _chat_query())

    assert captured_syscalls[0].get_priority() is None


def test_priority_is_applied_to_every_retry_of_one_request(captured_syscalls):
    """``_execute_syscall`` loops, rebuilding the syscall each iteration."""
    query = _chat_query()
    query._request_priority = "low"

    SyscallExecutor().execute_llm_syscall("agent_A", query)

    assert captured_syscalls, "no syscall was queued"
    assert all(
        syscall.get_priority() == "low" for syscall in captured_syscalls
    )


@pytest.mark.parametrize(
    "wire_value,expected",
    [
        ("high", PriorityLevel.HIGH),
        ("normal", PriorityLevel.NORMAL),
        ("low", PriorityLevel.LOW),
        (0, PriorityLevel.HIGH),
        (2, PriorityLevel.LOW),
    ],
)
def test_the_policy_reads_the_stamped_priority(
    captured_syscalls, wire_value: Any, expected: PriorityLevel
):
    """A value sent over HTTP becomes the level the policy actually sorts on."""
    query = _chat_query()
    query._request_priority = wire_value

    SyscallExecutor().execute_llm_syscall("agent_A", query)

    syscall = captured_syscalls[0]
    policy = PriorityPolicy(aging_interval=5)
    request = PendingRequest(
        payload=syscall,
        priority=syscall.get_priority(),
        arrival_tick=0,
        sequence=0,
    )

    assert policy.base_level(request) == int(expected)
