"""Priority and aging scheduling policy for the AIOS kernel.

This module holds the decision logic only: how a request's priority improves
while it waits, and which ready request should be dispatched next. It
deliberately imports nothing from AIOS so that:

* the policy can be unit-tested and benchmarked without installing the kernel
  dependencies (``cerebrum``, model backends) or starting a server, and
* a future port (``aios-rs``) can mirror it without inheriting the Python
  kernel's dependency graph.

``aios.scheduler.priority_scheduler.PriorityScheduler`` is the thin adapter
that feeds real ``aios.syscall.Syscall`` objects into this policy.

Priority model
--------------
AIOS already carries a ``priority`` field on every syscall
(``aios/syscall/__init__.py``) together with ``set_priority`` / ``get_priority``,
but nothing in the repository ever reads it. This policy is the reader.

Following the usual operating-systems convention, **a lower number means a more
urgent request**:

    HIGH   = 0
    NORMAL = 1
    LOW    = 2

Aging
-----
A pure priority policy starves: while a steady stream of HIGH requests keeps
arriving, a LOW request may never be dispatched. To prevent that, the effective
level of a waiting request improves over time::

    effective_level = max(0, base_level - floor(wait_ticks / aging_interval))

``wait_ticks`` counts *dispatch rounds*, not wall-clock seconds, so aging does
not depend on how long a single LLM call happens to take.

Because ``effective_level`` is clamped at 0 (= HIGH), a request reaches the top
level after ``base_level * aging_interval`` waiting rounds. From that round on
it cannot be overtaken by any request arriving later, because a later arrival
has a higher ``arrival_tick`` and therefore loses the tie-break. Only requests
that were already ready when it arrived can delay it, and each of those is
dispatched exactly once -- so no request waits forever. That is the starvation
bound implemented by :meth:`PriorityPolicy.starvation_bound` and verified in
``tests/modules/scheduler/test_priority_policy.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Dict, List, Optional, Sequence, Tuple


#: Accepted textual spellings for each level, all case-insensitive.
_ALIASES: Dict[str, "PriorityLevel"] = {}


class PriorityLevel(IntEnum):
    """Agent priority level. A lower value means a more urgent request."""

    HIGH = 0
    NORMAL = 1
    LOW = 2

    def __str__(self) -> str:
        return self.name

    @classmethod
    def from_name(cls, name: Any) -> Optional["PriorityLevel"]:
        """Resolve a textual priority such as ``"high"``.

        Returns ``None`` when the name is not recognised, so callers can decide
        whether to fall back to a default or to report an error.
        """
        if not isinstance(name, str):
            return None
        return _ALIASES.get(name.strip().lower())

    @classmethod
    def from_value(
        cls,
        value: Any,
        default: Optional["PriorityLevel"] = None,
    ) -> "PriorityLevel":
        """Normalise any caller-supplied priority into a :class:`PriorityLevel`.

        Accepts, in order:

        * a :class:`PriorityLevel` (returned unchanged),
        * a case-insensitive name such as ``"high"``, ``"normal"`` or ``"low"``
          (``"medium"``, ``"urgent"``, ``"background"`` and a few other
          spellings are accepted as aliases),
        * an integer *level*, where ``0`` is HIGH and ``2`` is LOW. Values
          outside that range are clamped rather than rejected: a malformed
          priority from an agent must not take the kernel down.

        Anything else falls back to ``default`` (NORMAL when not given).

        Note:
            ``aios/syscall/__init__.py`` documents ``set_priority(1)`` as
            "High priority", which conflicts with the level convention used
            here (``1`` is NORMAL). The level convention is kept because it
            matches :class:`PriorityLevel` and the aging formula; if the
            project settles on the other reading, only this method and the
            alias table need to change.
        """
        if default is None:
            default = cls.NORMAL
        if isinstance(value, PriorityLevel):
            return value
        if isinstance(value, str):
            named = cls.from_name(value)
            if named is not None:
                return named
            stripped = value.strip()
            if stripped.lstrip("+-").isdigit():
                value = int(stripped)
            else:
                return default
        if isinstance(value, int):
            return cls(max(int(cls.HIGH), min(int(value), int(cls.LOW))))
        return default


_ALIASES.update(
    {
        "high": PriorityLevel.HIGH,
        "hi": PriorityLevel.HIGH,
        "urgent": PriorityLevel.HIGH,
        "critical": PriorityLevel.HIGH,
        "interactive": PriorityLevel.HIGH,
        "normal": PriorityLevel.NORMAL,
        "med": PriorityLevel.NORMAL,
        "medium": PriorityLevel.NORMAL,
        "default": PriorityLevel.NORMAL,
        "low": PriorityLevel.LOW,
        "background": PriorityLevel.LOW,
        "bg": PriorityLevel.LOW,
        "batch": PriorityLevel.LOW,
    }
)


@dataclass(eq=False)
class PendingRequest:
    """A request sitting in the ready set, plus the fields the policy needs.

    ``eq=False`` keeps identity semantics, so ``list.remove`` on a ready set
    always removes exactly the object that was selected.

    Attributes:
        payload: The object to dispatch -- normally an ``LLMSyscall``.
        priority: Raw priority as supplied by the caller; normalised by the
            policy, so any of the :meth:`PriorityLevel.from_value` forms work.
        arrival_tick: Dispatch round in which the request became ready.
        sequence: Monotonic arrival counter, used to break ties between
            requests that became ready in the same round.
    """

    payload: Any
    priority: Any
    arrival_tick: int
    sequence: int

    def __repr__(self) -> str:
        name = getattr(self.payload, "agent_name", self.payload)
        return (
            f"PendingRequest(agent={name!r}, priority={self.priority!r}, "
            f"arrival_tick={self.arrival_tick}, sequence={self.sequence})"
        )


class PriorityPolicy:
    """Selects the most urgent ready request, with aging to prevent starvation.

    The policy is stateless with respect to time: the caller passes the current
    dispatch round (``now_tick``) into every call, which makes selection fully
    deterministic and trivially testable.

    Example:
        ```python
        policy = PriorityPolicy(aging_interval=3)
        ready = [
            PendingRequest(payload=low_agent, priority=PriorityLevel.LOW,
                           arrival_tick=0, sequence=0),
            PendingRequest(payload=high_agent, priority=PriorityLevel.HIGH,
                           arrival_tick=0, sequence=1),
        ]
        policy.select(ready, now_tick=0).payload   # -> high_agent
        policy.select(ready, now_tick=6).payload   # -> low_agent (aged to level 0)
        ```
    """

    def __init__(
        self,
        aging_interval: int = 5,
        default_priority: Any = PriorityLevel.NORMAL,
    ) -> None:
        """Initialise the policy.

        Args:
            aging_interval: Number of dispatch rounds a request must wait to
                gain one priority level. Must be >= 1.
            default_priority: Level used when a request carries no priority.

        Raises:
            ValueError: If ``aging_interval`` is not an integer >= 1.
        """
        if isinstance(aging_interval, bool) or not isinstance(aging_interval, int):
            raise ValueError(
                f"aging_interval must be an integer, got {aging_interval!r}"
            )
        if aging_interval < 1:
            raise ValueError(
                f"aging_interval must be >= 1, got {aging_interval!r}"
            )
        self.aging_interval: int = int(aging_interval)
        self.default_priority: PriorityLevel = PriorityLevel.from_value(
            default_priority
        )

    # ------------------------------------------------------------------
    # Priority and aging
    # ------------------------------------------------------------------
    def base_level(self, request: PendingRequest) -> int:
        """Return the request's level before aging (0 == HIGH)."""
        return int(
            PriorityLevel.from_value(request.priority, self.default_priority)
        )

    def wait_ticks(self, request: PendingRequest, now_tick: int) -> int:
        """Return how many dispatch rounds the request has been ready for."""
        return max(0, now_tick - request.arrival_tick)

    def effective_level(self, request: PendingRequest, now_tick: int) -> int:
        """Return the aged level: ``max(0, base_level - wait // aging_interval)``.

        The clamp at 0 is what makes the policy starvation-free: once a request
        reaches level 0 it cannot be improved any further, and it cannot be
        overtaken by a later arrival because of the arrival-time tie-break.
        """
        wait = self.wait_ticks(request, now_tick)
        return max(0, self.base_level(request) - wait // self.aging_interval)

    def sort_key(
        self,
        request: PendingRequest,
        now_tick: int,
    ) -> Tuple[int, int, int]:
        """Return the total dispatch order key.

        ``(effective_level, arrival_tick, sequence)`` -- best effective priority
        first, then the request that has waited longest, then arrival order as a
        deterministic final tie-break.
        """
        return (
            self.effective_level(request, now_tick),
            request.arrival_tick,
            request.sequence,
        )

    # ------------------------------------------------------------------
    # Selection
    # ------------------------------------------------------------------
    def select(
        self,
        ready: Sequence[PendingRequest],
        now_tick: int,
    ) -> Optional[PendingRequest]:
        """Return the request that should be dispatched next, or ``None``."""
        if not ready:
            return None
        return min(ready, key=lambda request: self.sort_key(request, now_tick))

    def rank(
        self,
        ready: Sequence[PendingRequest],
        now_tick: int,
    ) -> List[PendingRequest]:
        """Return the whole ready set in dispatch order (best first)."""
        return sorted(ready, key=lambda request: self.sort_key(request, now_tick))

    # ------------------------------------------------------------------
    # Starvation bound and observability
    # ------------------------------------------------------------------
    def starvation_bound(self, base_level: Any) -> int:
        """Rounds a request at ``base_level`` needs to reach level 0.

        This is the point after which no later arrival can be preferred to it,
        so it is the aging component of the worst-case wait.
        """
        level = PriorityLevel.from_value(base_level, self.default_priority)
        return int(level) * self.aging_interval

    @property
    def worst_case_aging_ticks(self) -> int:
        """Aging horizon for the lowest priority level (``LOW * interval``)."""
        return int(PriorityLevel.LOW) * self.aging_interval

    def explain(self, request: PendingRequest, now_tick: int) -> Dict[str, Any]:
        """Return the inputs and the result of the decision for one request.

        Intended for logging and for the evaluation harness: it makes the
        scheduler's reasoning inspectable without a debugger.
        """
        wait = self.wait_ticks(request, now_tick)
        base = self.base_level(request)
        return {
            "payload": request.payload,
            "base_priority": PriorityLevel.from_value(
                request.priority, self.default_priority
            ),
            "base_level": base,
            "wait_ticks": wait,
            "aging_steps": wait // self.aging_interval,
            "effective_level": max(0, base - wait // self.aging_interval),
            "arrival_tick": request.arrival_tick,
            "sequence": request.sequence,
        }

    def snapshot(
        self,
        ready: Sequence[PendingRequest],
        now_tick: int,
    ) -> List[Dict[str, Any]]:
        """Return :meth:`explain` for the whole ready set, in dispatch order."""
        return [self.explain(request, now_tick) for request in self.rank(ready, now_tick)]
