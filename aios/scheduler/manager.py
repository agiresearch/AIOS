"""Runtime ownership of the kernel's scheduling policy.

The policy is chosen at start-up from ``scheduler.policy`` in ``config.yaml``,
but it can also be changed while the kernel is running, through
``POST /core/scheduler/policy``. This module owns that: it holds the live
scheduler, remembers which policy and options produced it, and performs the
swap.

Why a swap needs care
---------------------
All four request queues are module-level globals, so a new scheduler instance
reads exactly the same queues as the old one -- which is what makes swapping
possible at all. What is *not* shared is a scheduler's own state. A
``PriorityScheduler`` holds requests it has already accepted off the queue in a
ready set, and each of those is a thread blocked on ``syscall.join()`` waiting
for a response. Dropping them would hang the calling agents, so the order is:

1. stop the old scheduler and wait for its threads to exit, which freezes its
   ready set;
2. hand any accepted-but-undispatched requests back to the global request queue;
3. start the new scheduler, which picks them up like any other arrival.

Stopping *before* draining is deliberate. Draining first would leave a window in
which the still-running old scheduler could re-admit a request that had just
been released, and then be stopped with it in hand -- losing it after all.

The new scheduler is constructed *before* the old one is stopped, so a bad
policy name or a bad option value is rejected while the running scheduler is
still untouched.

Example:
    ```python
    manager = SchedulerManager(components, scheduler_config, use_context_manager)
    manager.start()

    manager.describe()
    # {'policy': 'fifo', 'policy_class': 'FIFOScheduler', ...}

    manager.switch("priority", {"aging_interval": 3})
    # {'previous': 'fifo', 'policy': 'priority', 'released_requests': 0, ...}
    ```
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Callable, Dict, Mapping, Optional

from .registry import (
    POLICY_PRIORITY,
    POLICY_ROUND_ROBIN,
    available_policies,
    build_scheduler_params,
    create_scheduler,
    normalise_policy_name,
    policy_options,
)


class SchedulerManager:
    """Owns the running scheduler and swaps it when the policy changes.

    Attributes:
        components: The kernel's component dict (``llms``, ``memory``,
            ``storage``, ``tool``). The schedulers share these; only the
            dispatch rule changes when the policy changes.
    """

    def __init__(
        self,
        components: Mapping[str, Any],
        scheduler_config: Optional[Mapping[str, Any]] = None,
        use_context_manager: bool = False,
        queue_getters: Optional[Mapping[str, Callable[[], Any]]] = None,
        release_llm_syscall: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """Initialise the manager.

        Args:
            components: Kernel components, passed to each scheduler.
            scheduler_config: The ``scheduler`` section of ``config.yaml``.
            use_context_manager: Value of ``llms.use_context_manager``. Naming no
                policy while this is set keeps the historical round-robin
                choice, because context switching is implemented there.
            queue_getters: Optional override for the request-queue readers.
                Defaults to the kernel's global queues; tests pass their own.
            release_llm_syscall: Optional override for putting an
                accepted-but-undispatched LLM request back on the request queue.
                Defaults to the kernel's global adder; tests pass their own.
        """
        self._components = components
        self._config: Dict[str, Any] = dict(scheduler_config or {})
        self._use_context_manager = use_context_manager
        self._queue_getters = dict(queue_getters or {})
        self._release_llm_syscall = release_llm_syscall

        self._lock = Lock()
        self._scheduler: Optional[Any] = None
        self._policy: Optional[str] = None
        self._options: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    @property
    def policy(self) -> Optional[str]:
        """Canonical name of the running policy, or ``None`` before ``start``."""
        return self._policy

    @property
    def scheduler(self) -> Optional[Any]:
        """The live scheduler instance, or ``None`` before ``start``."""
        return self._scheduler

    @property
    def options(self) -> Dict[str, Any]:
        """Options the running policy was constructed with."""
        return dict(self._options)

    def describe(self) -> Dict[str, Any]:
        """Return a serialisable summary of the running configuration.

        Used by ``GET /core/scheduler`` so a policy in effect can be checked
        without reading start-up output or inferring it from log prefixes.
        """
        scheduler = self._scheduler
        dispatched = getattr(scheduler, "dispatched_count", None)
        return {
            "policy": self._policy,
            "policy_class": type(scheduler).__name__ if scheduler else None,
            "options": dict(self._options),
            "dispatched_llm_requests": dispatched,
            "available_policies": list(available_policies()),
            # Surfaced because it is the one configuration combination that
            # silently changes which policy runs when none is named.
            "use_context_manager": self._use_context_manager,
        }

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _build(self, policy: str, options: Mapping[str, Any]) -> Any:
        """Construct (but do not start) a scheduler for ``policy``.

        Raises:
            ValueError: If the policy name is unknown or an option is invalid.
                Raised before the running scheduler is touched.
        """
        config: Dict[str, Any] = dict(self._config)
        config["policy"] = policy

        if options:
            section = config.get(policy)
            merged = dict(section) if isinstance(section, Mapping) else {}
            merged.update(options)
            config[policy] = merged

        name, params = build_scheduler_params(
            self._components,
            config,
            use_context_manager=self._use_context_manager,
        )
        # An explicitly injected getter wins over the kernel's global queue, so
        # a test can drive the manager without touching kernel state.
        params.update(self._queue_getters)
        return create_scheduler(name, **params)

    def _release(self, requests: Any) -> int:
        """Put accepted-but-undispatched LLM requests back on the request queue.

        Returns:
            How many requests were re-queued.
        """
        released = 0
        for syscall in requests:
            if self._release_llm_syscall is not None:
                self._release_llm_syscall(syscall)
            else:
                from aios.hooks.stores._global import (
                    global_llm_req_queue_add_message,
                )

                global_llm_req_queue_add_message(syscall)
            released += 1
        return released

    def start(self) -> Any:
        """Build and start the scheduler named by configuration.

        Returns:
            The started scheduler.
        """
        with self._lock:
            name, params = build_scheduler_params(
                self._components,
                self._config,
                use_context_manager=self._use_context_manager,
            )
            params.update(self._queue_getters)
            scheduler = create_scheduler(name, **params)
            scheduler.start()

            self._scheduler = scheduler
            self._policy = name
            self._options = policy_options(self._config, name)
            return scheduler

    def switch(
        self,
        policy: str,
        options: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Replace the running scheduler with one for ``policy``.

        Requests already accepted but not yet dispatched are re-queued, so no
        waiting agent is left blocked.

        Args:
            policy: Canonical policy name or accepted alias.
            options: Options for the new policy, merged over the ones in
                configuration. Keys the policy does not declare are ignored, so
                a leftover key cannot break the switch.

        Returns:
            A summary: the new and previous policy, the options actually
            applied, and how many requests were re-queued.

        Raises:
            ValueError: If the policy name is unknown, or an option value is
                invalid. The running scheduler is left untouched.
        """
        with self._lock:
            # Validate and construct first. If either fails, the kernel keeps
            # running the policy it already had.
            new_policy = normalise_policy_name(policy)
            config = dict(self._config)
            config["policy"] = new_policy
            if options:
                section = config.get(new_policy)
                merged = dict(section) if isinstance(section, Mapping) else {}
                merged.update(options)
                config[new_policy] = merged
            applied_options = policy_options(config, new_policy)

            new_scheduler = self._build(new_policy, options or {})

            previous = self._policy
            old_scheduler = self._scheduler

            # Stop first: until the threads exit the ready set is still moving,
            # and anything released now could be re-admitted by the scheduler
            # we are about to replace.
            if old_scheduler is not None:
                old_scheduler.stop()

            released = 0
            drain = getattr(old_scheduler, "drain_pending_syscalls", None)
            if drain is not None:
                released = self._release(drain())

            new_scheduler.start()

            self._scheduler = new_scheduler
            self._policy = new_policy
            self._options = applied_options

            return {
                "policy": new_policy,
                "previous": previous,
                "policy_class": type(new_scheduler).__name__,
                "options": applied_options,
                "released_requests": released,
            }

    def stop(self) -> None:
        """Stop the running scheduler, if any."""
        with self._lock:
            if self._scheduler is not None:
                self._scheduler.stop()
            self._scheduler = None
            self._policy = None


__all__ = ["SchedulerManager", "POLICY_PRIORITY", "POLICY_ROUND_ROBIN"]
