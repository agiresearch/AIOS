"""Tests for choosing the scheduling policy from configuration.

``aios.scheduler.registry`` imports only the standard library -- policy classes
are imported lazily inside ``create_scheduler`` -- so configuration handling can
be verified without ``cerebrum``, a model backend or a running kernel. The
construction half of the registry is covered in
``test_priority_scheduler.py``, where the kernel is available.

The behaviour that matters most here is *backwards compatibility*: naming no
policy must reproduce exactly what ``runtime/launch.py`` did before the policy
became configurable.
"""

from __future__ import annotations

import pytest

from aios.scheduler.registry import (
    DEFAULT_POLICY,
    POLICY_FIFO,
    POLICY_PRIORITY,
    POLICY_ROUND_ROBIN,
    SUPPORTED_POLICIES,
    available_policies,
    normalise_policy_name,
    policy_options,
    resolve_policy_name,
)


# ----------------------------------------------------------------------
# Available policies
# ----------------------------------------------------------------------
def test_available_policies_lists_every_selectable_policy():
    assert available_policies() == SUPPORTED_POLICIES
    assert set(SUPPORTED_POLICIES) == {POLICY_FIFO, POLICY_ROUND_ROBIN, POLICY_PRIORITY}


def test_default_policy_is_fifo():
    """Naming no policy must not change the existing out-of-the-box behaviour."""
    assert DEFAULT_POLICY == POLICY_FIFO


# ----------------------------------------------------------------------
# Resolving the policy from config
# ----------------------------------------------------------------------
def test_no_policy_configured_keeps_the_historical_behaviour():
    assert resolve_policy_name({}, use_context_manager=False) == POLICY_FIFO
    assert resolve_policy_name({}, use_context_manager=True) == POLICY_ROUND_ROBIN


@pytest.mark.parametrize("scheduler_config", [None, {}, {"log_mode": "console"}])
def test_a_missing_scheduler_section_is_tolerated(scheduler_config):
    assert resolve_policy_name(scheduler_config) == DEFAULT_POLICY


@pytest.mark.parametrize("value", [None, "", "   "])
def test_an_empty_policy_value_is_treated_as_unset(value):
    assert resolve_policy_name({"policy": value}) == DEFAULT_POLICY
    assert (
        resolve_policy_name({"policy": value}, use_context_manager=True)
        == POLICY_ROUND_ROBIN
    )


def test_an_explicit_policy_wins_over_context_management():
    """The configured policy is authoritative, even with context management on."""
    config = {"policy": "priority"}
    assert resolve_policy_name(config, use_context_manager=True) == POLICY_PRIORITY
    assert resolve_policy_name(config, use_context_manager=False) == POLICY_PRIORITY


@pytest.mark.parametrize(
    "value,expected",
    [
        ("fifo", POLICY_FIFO),
        ("FIFO", POLICY_FIFO),
        ("fcfs", POLICY_FIFO),
        ("first_come_first_served", POLICY_FIFO),
        ("round_robin", POLICY_ROUND_ROBIN),
        ("round-robin", POLICY_ROUND_ROBIN),
        (" Round Robin ", POLICY_ROUND_ROBIN),
        ("RoundRobin", POLICY_ROUND_ROBIN),
        ("rr", POLICY_ROUND_ROBIN),
        ("priority", POLICY_PRIORITY),
        ("PRIORITY", POLICY_PRIORITY),
        ("prio", POLICY_PRIORITY),
    ],
)
def test_policy_names_are_normalised(value, expected):
    assert normalise_policy_name(value) == expected
    assert resolve_policy_name({"policy": value}) == expected


def test_unknown_policy_is_rejected_with_the_valid_names():
    with pytest.raises(ValueError, match="Unknown scheduling policy"):
        normalise_policy_name("lottery")

    # The message tells the operator what to write instead.
    with pytest.raises(ValueError) as error:
        resolve_policy_name({"policy": "lottery"})
    for policy in SUPPORTED_POLICIES:
        assert policy in str(error.value)


def test_non_string_policy_is_rejected():
    with pytest.raises(ValueError, match="must be a string"):
        normalise_policy_name(3)


# ----------------------------------------------------------------------
# Per-policy options
# ----------------------------------------------------------------------
def test_priority_options_are_read_from_the_priority_section():
    config = {
        "policy": "priority",
        "priority": {"aging_interval": 3, "default_priority": "high"},
    }
    assert policy_options(config, POLICY_PRIORITY) == {
        "aging_interval": 3,
        "default_priority": "high",
    }


@pytest.mark.parametrize(
    "policy,section,expected",
    [
        (POLICY_FIFO, {"batch_interval": 0.1}, {"batch_interval": 0.1}),
        (POLICY_ROUND_ROBIN, {"time_slice": 2}, {"time_slice": 2}),
        (POLICY_PRIORITY, {"aging_interval": 10}, {"aging_interval": 10}),
    ],
)
def test_each_policy_reads_its_own_options(policy, section, expected):
    assert policy_options({policy: section}, policy) == expected


def test_undeclared_option_keys_are_ignored():
    """A stale key from another policy must not crash the kernel."""
    config = {
        "priority": {"aging_interval": 4, "time_slice": 9, "nonsense": True},
    }
    assert policy_options(config, POLICY_PRIORITY) == {"aging_interval": 4}


@pytest.mark.parametrize(
    "config",
    [None, {}, {"priority": None}, {"priority": "not-a-mapping"}, {"priority": []}],
)
def test_missing_or_malformed_option_sections_yield_no_options(config):
    assert policy_options(config, POLICY_PRIORITY) == {}


def test_options_can_be_read_through_an_alias():
    config = {"round_robin": {"time_slice": 0.5}}
    assert policy_options(config, "rr") == {"time_slice": 0.5}


def test_options_do_not_mutate_the_configuration():
    config = {"priority": {"aging_interval": 4}}
    policy_options(config, POLICY_PRIORITY)
    assert config == {"priority": {"aging_interval": 4}}


def test_an_unknown_policy_has_no_options():
    with pytest.raises(ValueError):
        policy_options({}, "lottery")
