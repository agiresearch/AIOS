"""Tests for the priority and aging scheduling policy.

``aios/scheduler/priority_policy.py`` imports only the standard library, so
these tests run without ``cerebrum``, a model backend or a running kernel.

Covered:

* priority ordering (HIGH before NORMAL before LOW),
* deterministic tie-breaking by arrival time and arrival order,
* the aging progression and its clamp at level 0,
* the starvation bound, including an adversarial saturated arrival stream,
* the invariant that a later arrival can never overtake a request that has
  aged out.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from aios.scheduler.priority_policy import (
    PendingRequest,
    PriorityLevel,
    PriorityPolicy,
)


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def request(
    priority,
    arrival_tick: int = 0,
    sequence: int = 0,
    name: str = "agent",
) -> PendingRequest:
    """Build a PendingRequest whose payload is a readable agent name."""
    return PendingRequest(
        payload=name,
        priority=priority,
        arrival_tick=arrival_tick,
        sequence=sequence,
    )


def simulate(policy: PriorityPolicy, arrivals, max_ticks: int = 200):
    """Dispatch one ready request per tick and return the dispatch log.

    This is the scheduling model the kernel adapter implements: each tick, newly
    arrived requests are admitted, one request is dispatched, and the tick
    advances. It lets the policy be evaluated without any AIOS runtime.

    Args:
        policy: The policy under test.
        arrivals: Mapping ``tick -> list[PendingRequest]`` of requests admitted
            at that tick. Each request's ``arrival_tick`` must match its key.
        max_ticks: Safety bound.

    Returns:
        List of ``(tick, payload)`` tuples in dispatch order.
    """
    ready = []
    dispatched = []
    now = 0
    while now < max_ticks:
        ready.extend(arrivals.get(now, []))
        chosen = policy.select(ready, now)
        if chosen is None:
            if not any(tick >= now for tick in arrivals):
                break
            now += 1
            continue
        ready.remove(chosen)
        dispatched.append((now, chosen.payload))
        now += 1
    return dispatched


def dispatch_order(log):
    return [name for _, name in log]


# ----------------------------------------------------------------------
# Priority ordering
# ----------------------------------------------------------------------
def test_high_is_dispatched_before_normal_and_low():
    policy = PriorityPolicy(aging_interval=10)
    ready = [
        request(PriorityLevel.LOW, 0, 0, "low"),
        request(PriorityLevel.NORMAL, 0, 1, "normal"),
        request(PriorityLevel.HIGH, 0, 2, "high"),
    ]
    assert [r.payload for r in policy.rank(ready, 0)] == ["high", "normal", "low"]


def test_priority_overrides_arrival_order():
    """The point of the feature: an urgent latecomer is served first."""
    policy = PriorityPolicy(aging_interval=10)
    arrivals = {
        0: [
            request(PriorityLevel.LOW, 0, 0, "report_agent"),
            request(PriorityLevel.HIGH, 0, 1, "chat_agent"),
        ]
    }

    log = simulate(policy, arrivals)
    assert dispatch_order(log) == ["chat_agent", "report_agent"]

    # ...whereas serving in arrival order (what FIFOScheduler does) would not.
    arrival_order = [
        r.payload for r in sorted(arrivals[0], key=lambda r: r.sequence)
    ]
    assert arrival_order == ["report_agent", "chat_agent"]


def test_equal_priority_is_dispatched_in_arrival_order():
    policy = PriorityPolicy(aging_interval=10)
    ready = [
        request(PriorityLevel.NORMAL, 0, 2, "third"),
        request(PriorityLevel.NORMAL, 0, 0, "first"),
        request(PriorityLevel.NORMAL, 0, 1, "second"),
    ]
    assert [r.payload for r in policy.rank(ready, 0)] == ["first", "second", "third"]


def test_waiting_longer_wins_within_the_same_effective_level():
    policy = PriorityPolicy(aging_interval=100)
    ready = [
        request(PriorityLevel.HIGH, arrival_tick=7, sequence=1, name="newer"),
        request(PriorityLevel.HIGH, arrival_tick=3, sequence=2, name="older"),
    ]
    assert policy.select(ready, now_tick=7).payload == "older"


def test_arrival_sequence_breaks_a_tie_on_the_same_tick():
    policy = PriorityPolicy(aging_interval=100)
    ready = [
        request(PriorityLevel.HIGH, arrival_tick=4, sequence=9, name="second"),
        request(PriorityLevel.HIGH, arrival_tick=4, sequence=4, name="first"),
    ]
    assert policy.select(ready, now_tick=4).payload == "first"


def test_select_on_an_empty_ready_set_returns_none():
    assert PriorityPolicy().select([], 0) is None


# ----------------------------------------------------------------------
# Aging
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "wait_ticks,expected_level",
    [
        (0, 2), (1, 2), (2, 2),   # LOW, still inside the first interval
        (3, 1), (4, 1), (5, 1),   # promoted once
        (6, 0), (7, 0), (11, 0),  # promoted twice, then clamped
        (100, 0),
    ],
)
def test_aging_progression_for_a_low_priority_request(wait_ticks, expected_level):
    policy = PriorityPolicy(aging_interval=3)
    low = request(PriorityLevel.LOW, arrival_tick=0, sequence=0, name="low")
    assert policy.effective_level(low, now_tick=wait_ticks) == expected_level


def test_aging_never_improves_a_request_beyond_high():
    policy = PriorityPolicy(aging_interval=1)
    low = request(PriorityLevel.LOW, arrival_tick=0)
    assert policy.effective_level(low, now_tick=50) == int(PriorityLevel.HIGH)


def test_aging_does_not_apply_before_arrival():
    policy = PriorityPolicy(aging_interval=2)
    late = request(PriorityLevel.NORMAL, arrival_tick=10)
    assert policy.wait_ticks(late, now_tick=4) == 0
    assert policy.effective_level(late, now_tick=4) == int(PriorityLevel.NORMAL)


def test_aging_promotes_a_starved_request_above_a_fresh_one():
    policy = PriorityPolicy(aging_interval=2)
    old_low = request(PriorityLevel.LOW, arrival_tick=0, sequence=0, name="old_low")
    new_normal = request(
        PriorityLevel.NORMAL, arrival_tick=2, sequence=1, name="new_normal"
    )

    # Two rounds of waiting lift the LOW request to NORMAL (2 - 2 // 2 == 1).
    assert policy.effective_level(old_low, now_tick=2) == int(PriorityLevel.NORMAL)
    # ...and the request that has waited longer wins the resulting tie.
    assert policy.select([new_normal, old_low], now_tick=2).payload == "old_low"


# ----------------------------------------------------------------------
# Starvation bound
# ----------------------------------------------------------------------
def test_worst_case_aging_ticks_is_low_times_the_interval():
    assert PriorityPolicy(aging_interval=4).worst_case_aging_ticks == 8
    assert PriorityPolicy(aging_interval=1).worst_case_aging_ticks == 2


@pytest.mark.parametrize("level,expected", [(0, 0), (1, 5), (2, 10)])
def test_starvation_bound_scales_with_the_base_level(level, expected):
    policy = PriorityPolicy(aging_interval=5)
    assert policy.starvation_bound(level) == expected


def test_a_low_request_is_dispatched_within_the_starvation_bound():
    """Adversarial workload: a HIGH request arrives every single round."""
    interval = 3
    policy = PriorityPolicy(aging_interval=interval)
    arrivals = {
        0: [
            request(PriorityLevel.LOW, 0, 0, "low"),
            request(PriorityLevel.HIGH, 0, 1, "high0"),
        ]
    }
    for tick in range(1, 40):
        arrivals[tick] = [
            request(PriorityLevel.HIGH, tick, 100 + tick, f"high{tick}")
        ]

    log = simulate(policy, arrivals)
    dispatched_at = dict((name, tick) for tick, name in log)

    assert "low" in dispatched_at, "the LOW request was starved"
    assert (
        dispatched_at["low"]
        == policy.starvation_bound(PriorityLevel.LOW)
        == 2 * interval
    )


def test_without_aging_the_same_workload_starves_the_low_request():
    """Why aging is required at all: a huge interval is equivalent to none."""
    policy = PriorityPolicy(aging_interval=10 ** 6)
    arrivals = {
        0: [
            request(PriorityLevel.LOW, 0, 0, "low"),
            request(PriorityLevel.HIGH, 0, 1, "high0"),
        ]
    }
    for tick in range(1, 40):
        arrivals[tick] = [
            request(PriorityLevel.HIGH, tick, 100 + tick, f"high{tick}")
        ]

    log = simulate(policy, arrivals, max_ticks=40)
    assert "low" not in dispatch_order(log)


@given(
    interval=st.integers(min_value=1, max_value=8),
    high_per_tick=st.integers(min_value=1, max_value=3),
)
@settings(max_examples=40, deadline=None)
def test_bound_holds_for_every_aging_interval_and_arrival_rate(interval, high_per_tick):
    """Property: the dispatch tick of a LOW request equals the bound exactly.

    Once the LOW request reaches level 0 it wins every tie against requests that
    arrived later, so the arrival rate of HIGH requests cannot delay it beyond
    ``LOW * aging_interval``.
    """
    policy = PriorityPolicy(aging_interval=interval)
    arrivals = {0: [request(PriorityLevel.LOW, 0, 0, "low")]}
    arrivals[0].append(request(PriorityLevel.HIGH, 0, 1, "high0"))
    for tick in range(1, 60):
        arrivals[tick] = [
            request(PriorityLevel.HIGH, tick, 100 + tick * 10 + i, f"high{tick}-{i}")
            for i in range(high_per_tick)
        ]

    log = simulate(policy, arrivals)
    dispatched_at = dict((name, tick) for tick, name in log)

    assert "low" in dispatched_at
    assert dispatched_at["low"] == 2 * interval


@given(
    interval=st.integers(min_value=1, max_value=6),
    high_per_tick=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=40, deadline=None)
def test_no_later_arrival_is_dispatched_first_after_a_request_ages_out(
    interval, high_per_tick
):
    """Property: aging out is final -- later arrivals cannot overtake.

    This is the starvation-freedom argument in test form: from the round a
    request reaches level 0, only requests that were already waiting when it
    arrived can precede it.
    """
    policy = PriorityPolicy(aging_interval=interval)
    low = request(PriorityLevel.LOW, 0, 0, "low")
    arrivals = {0: [low, request(PriorityLevel.HIGH, 0, 1, "high0")]}
    for tick in range(1, 60):
        arrivals[tick] = [
            request(PriorityLevel.HIGH, tick, 100 + tick * 10 + i, f"high{tick}-{i}")
            for i in range(high_per_tick)
        ]
    arrival_of = {
        r.payload: r.arrival_tick for requests in arrivals.values() for r in requests
    }

    log = simulate(policy, arrivals)
    dispatched_at = dict((name, tick) for tick, name in log)
    assert "low" in dispatched_at

    aged_out_tick = low.arrival_tick + policy.starvation_bound(PriorityLevel.LOW)
    low_tick = dispatched_at["low"]
    for tick, name in log:
        if name == "low" or tick <= aged_out_tick:
            continue
        if arrival_of[name] > arrival_of["low"]:
            assert tick > low_tick


# ----------------------------------------------------------------------
# Priority normalisation
# ----------------------------------------------------------------------
@pytest.mark.parametrize(
    "value,expected",
    [
        (PriorityLevel.HIGH, PriorityLevel.HIGH),
        ("high", PriorityLevel.HIGH),
        ("HIGH", PriorityLevel.HIGH),
        (" High ", PriorityLevel.HIGH),
        ("urgent", PriorityLevel.HIGH),
        (0, PriorityLevel.HIGH),
        ("normal", PriorityLevel.NORMAL),
        ("medium", PriorityLevel.NORMAL),
        (1, PriorityLevel.NORMAL),
        ("low", PriorityLevel.LOW),
        ("background", PriorityLevel.LOW),
        (2, PriorityLevel.LOW),
        (0.5, PriorityLevel.NORMAL),   # floats are not levels -> default
        ("nonsense", PriorityLevel.NORMAL),
        (None, PriorityLevel.NORMAL),
    ],
)
def test_from_value_normalises_supported_forms(value, expected):
    assert PriorityLevel.from_value(value) is expected


@pytest.mark.parametrize("value,expected", [(-5, PriorityLevel.HIGH), (99, PriorityLevel.LOW)])
def test_out_of_range_integers_are_clamped_not_rejected(value, expected):
    assert PriorityLevel.from_value(value) is expected


def test_integer_strings_are_read_as_levels():
    assert PriorityLevel.from_value("0") is PriorityLevel.HIGH
    assert PriorityLevel.from_value("2") is PriorityLevel.LOW


def test_from_name_returns_none_for_unknown_names():
    assert PriorityLevel.from_name("nonsense") is None
    assert PriorityLevel.from_name(3) is None


def test_unset_priority_falls_back_to_the_policy_default():
    policy = PriorityPolicy(aging_interval=5, default_priority=PriorityLevel.HIGH)
    unset = request(None, 0, 0, "no_priority")
    assert policy.base_level(unset) == int(PriorityLevel.HIGH)


# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
@pytest.mark.parametrize("bad_interval", [0, -1, 2.5, "5", None, True])
def test_invalid_aging_interval_is_rejected(bad_interval):
    with pytest.raises(ValueError, match="aging_interval"):
        PriorityPolicy(aging_interval=bad_interval)


# ----------------------------------------------------------------------
# Observability
# ----------------------------------------------------------------------
def test_explain_reports_the_dispatch_decision():
    policy = PriorityPolicy(aging_interval=3)
    low = request(PriorityLevel.LOW, arrival_tick=0, sequence=7, name="low")
    details = policy.explain(low, now_tick=4)

    assert details["base_priority"] is PriorityLevel.LOW
    assert details["base_level"] == 2
    assert details["wait_ticks"] == 4
    assert details["aging_steps"] == 1
    assert details["effective_level"] == 1
    assert details["sequence"] == 7


def test_snapshot_is_in_dispatch_order_and_covers_the_ready_set():
    policy = PriorityPolicy(aging_interval=3)
    ready = [
        request(PriorityLevel.LOW, 0, 0, "low"),
        request(PriorityLevel.HIGH, 4, 1, "high"),
    ]
    snapshot = policy.snapshot(ready, now_tick=6)

    # The waiting LOW request has aged from level 2 to level 0 and now precedes
    # a HIGH request that arrived later.
    assert [entry["payload"] for entry in snapshot] == ["low", "high"]
    assert snapshot[0]["base_priority"] is PriorityLevel.LOW
    assert snapshot[0]["effective_level"] == 0
    assert snapshot[1]["effective_level"] == 0


def test_pending_request_repr_is_readable():
    assert "agent='chat_agent'" in repr(
        request(PriorityLevel.HIGH, 0, 0, "chat_agent")
    )
