"""Scheduler policy selection and construction for AIOS.

This module is the single place that turns the ``scheduler`` section of
``config.yaml`` into a scheduler instance::

    scheduler:
      log_mode: "console"     # choose from [console, file]
      policy: "priority"      # choose from [fifo, round_robin, priority]

      # Options for the policy above; only the keys the policy declares are read.
      fifo:
        batch_interval: 1.0
      round_robin:
        time_slice: 1.0
      priority:
        aging_interval: 5
        default_priority: "normal"

Two things motivated it:

* **Policy and mechanism separation.** ``runtime/launch.py`` previously decided
  the policy implicitly, from the unrelated ``use_context_manager`` flag. The
  policy is now named in configuration, and naming none keeps the old behaviour.
* **Extensibility.** A new policy is one entry in :data:`_POLICY_BUILDERS`
  rather than another branch in the kernel launcher.

Policy classes are imported lazily inside :func:`create_scheduler`, so validating
a configuration value does not drag in ``cerebrum`` or the model backends. The
only function here that touches the kernel is :func:`resolve_queue_getters`, and
it imports the request queues lazily as well.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Tuple

#: Canonical policy keys. These are the strings accepted in ``scheduler.policy``.
POLICY_FIFO = "fifo"
POLICY_ROUND_ROBIN = "round_robin"
POLICY_PRIORITY = "priority"

#: Policy used when ``scheduler.policy`` is absent and context management is off.
DEFAULT_POLICY = POLICY_FIFO

#: Every selectable policy, in documentation order.
SUPPORTED_POLICIES: Tuple[str, ...] = (
    POLICY_FIFO,
    POLICY_ROUND_ROBIN,
    POLICY_PRIORITY,
)

#: Alternative spellings accepted in configuration, all case-insensitive.
_POLICY_ALIASES: Dict[str, str] = {
    "fifo": POLICY_FIFO,
    "fcfs": POLICY_FIFO,
    "first_come_first_served": POLICY_FIFO,
    "round_robin": POLICY_ROUND_ROBIN,
    "roundrobin": POLICY_ROUND_ROBIN,
    "rr": POLICY_ROUND_ROBIN,
    "priority": POLICY_PRIORITY,
    "prio": POLICY_PRIORITY,
}

#: Per-policy constructor arguments that may be set in configuration. Anything
#: else under the policy's config section is ignored, so a stale key left over
#: from another policy cannot take the kernel down.
_POLICY_OPTIONS: Dict[str, Tuple[str, ...]] = {
    POLICY_FIFO: ("batch_interval",),
    POLICY_ROUND_ROBIN: ("time_slice",),
    POLICY_PRIORITY: ("aging_interval", "default_priority"),
}

#: Names of the queue getters a scheduler is constructed with.
_QUEUE_GETTERS: Tuple[str, ...] = (
    "get_llm_syscall",
    "get_memory_syscall",
    "get_storage_syscall",
    "get_tool_syscall",
)


def available_policies() -> Tuple[str, ...]:
    """Return the canonical policy names that can be set in configuration."""
    return SUPPORTED_POLICIES


def normalise_policy_name(value: Any) -> str:
    """Return the canonical policy key for a configured value.

    Accepts the canonical names plus a few spellings (``fcfs``, ``rr``,
    ``round-robin``, ``PRIORITY``).

    Raises:
        ValueError: If the name is not a known policy. Failing loudly is
            deliberate: silently falling back to FIFO would leave an operator
            believing their policy is in effect when it is not.
    """
    if not isinstance(value, str):
        raise ValueError(
            f"scheduler.policy must be a string, got {value!r}. "
            f"Choose from {list(SUPPORTED_POLICIES)}."
        )
    key = value.strip().lower().replace("-", "_").replace(" ", "_")
    policy = _POLICY_ALIASES.get(key)
    if policy is None:
        raise ValueError(
            f"Unknown scheduling policy {value!r}. "
            f"Choose from {list(SUPPORTED_POLICIES)}."
        )
    return policy


def resolve_policy_name(
    scheduler_config: Optional[Mapping[str, Any]],
    use_context_manager: bool = False,
) -> str:
    """Return the policy to use for a ``scheduler`` config section.

    ``scheduler.policy`` wins when it is set. When it is absent or empty the
    historical behaviour is preserved: ``round_robin`` if context management is
    enabled (context switching is implemented by ``RRScheduler``), otherwise
    ``fifo``.

    Args:
        scheduler_config: The ``scheduler`` section of ``config.yaml``.
        use_context_manager: Value of ``llms.use_context_manager``.

    Returns:
        A canonical policy name.
    """
    configured = (scheduler_config or {}).get("policy")
    if configured is not None and str(configured).strip() != "":
        return normalise_policy_name(configured)
    return POLICY_ROUND_ROBIN if use_context_manager else DEFAULT_POLICY


def policy_options(
    scheduler_config: Optional[Mapping[str, Any]],
    policy_name: str,
) -> Dict[str, Any]:
    """Return the constructor arguments configured for one policy.

    Reads the ``scheduler.<policy_name>`` section and keeps only the keys that
    policy declares (see :data:`_POLICY_OPTIONS`).

    Example:
        ```python
        policy_options({"priority": {"aging_interval": 5, "nonsense": 1}},
                       "priority")
        # -> {"aging_interval": 5}
        ```
    """
    policy = normalise_policy_name(policy_name)
    section = (scheduler_config or {}).get(policy)
    if not isinstance(section, Mapping):
        return {}
    return {
        key: section[key]
        for key in _POLICY_OPTIONS.get(policy, ())
        if key in section
    }


def resolve_queue_getters(params: Mapping[str, Any]) -> Dict[str, Any]:
    """Fill missing queue getters with the kernel's global request queues.

    Mirrors what the hook functions in ``aios/hooks/modules/scheduler.py`` do,
    so a scheduler built from ``config.yaml`` reads from exactly the same queues
    as one built through ``useFIFOScheduler``.

    Args:
        params: Scheduler constructor arguments.

    Returns:
        A new dict; ``params`` is not modified.
    """
    from aios.hooks.stores._global import (
        global_llm_req_queue_get_message,
        global_memory_req_queue_get_message,
        global_storage_req_queue_get_message,
        global_tool_req_queue_get_message,
    )

    defaults = {
        "get_llm_syscall": global_llm_req_queue_get_message,
        "get_memory_syscall": global_memory_req_queue_get_message,
        "get_storage_syscall": global_storage_req_queue_get_message,
        "get_tool_syscall": global_tool_req_queue_get_message,
    }

    resolved = dict(params)
    for name in _QUEUE_GETTERS:
        if resolved.get(name) is None:
            resolved[name] = defaults[name]
    return resolved


def create_scheduler(policy_name: str, **params: Any) -> Any:
    """Construct, but do not start, the scheduler for a policy name.

    Args:
        policy_name: Canonical name or accepted alias.
        **params: Constructor arguments for the scheduler class.

    Returns:
        An unstarted scheduler instance.

    Raises:
        ValueError: If ``policy_name`` is not a known policy.
    """
    policy = normalise_policy_name(policy_name)

    if policy == POLICY_FIFO:
        from .fifo_scheduler import FIFOScheduler

        return FIFOScheduler(**params)

    if policy == POLICY_ROUND_ROBIN:
        from .rr_scheduler import RRScheduler

        return RRScheduler(**params)

    if policy == POLICY_PRIORITY:
        from .priority_scheduler import PriorityScheduler

        return PriorityScheduler(**params)

    # Unreachable: normalise_policy_name only returns canonical names.
    raise ValueError(f"No builder registered for policy {policy!r}.")


def build_scheduler_params(
    components: Mapping[str, Any],
    scheduler_config: Optional[Mapping[str, Any]] = None,
    use_context_manager: bool = False,
) -> Tuple[str, Dict[str, Any]]:
    """Build the policy name and constructor arguments from configuration.

    This is the one call a launcher needs: it resolves the policy, collects the
    policy-specific options, and fills in the kernel's request queues.

    Args:
        components: Component dict holding ``llms``, ``memory``, ``storage``
            and ``tool``.
        scheduler_config: The ``scheduler`` section of ``config.yaml``.
        use_context_manager: Value of ``llms.use_context_manager``.

    Returns:
        ``(policy_name, params)`` where ``params`` is ready for
        :func:`create_scheduler`.
    """
    config = scheduler_config or {}
    policy = resolve_policy_name(config, use_context_manager=use_context_manager)

    params: Dict[str, Any] = {
        "llm": components["llms"],
        "memory_manager": components["memory"],
        "storage_manager": components["storage"],
        "tool_manager": components["tool"],
        "log_mode": config.get("log_mode", "console"),
        "get_llm_syscall": None,
        "get_memory_syscall": None,
        "get_storage_syscall": None,
        "get_tool_syscall": None,
    }
    params.update(policy_options(config, policy))
    return policy, resolve_queue_getters(params)
