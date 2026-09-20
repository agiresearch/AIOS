#!/usr/bin/env python3
"""Gantt-chart demo: compare AIOS scheduling policies by flipping one config line.

The scheduler is the part of an operating system that decides *whose turn it is*.
This script runs the same workload through the real AIOS scheduler classes and
prints, for each policy:

* a Gantt chart of who held the LLM and for how long,
* per-agent response time and waiting time,
* the number of dispatch rounds a low-priority request had to wait, checked
  against the starvation bound ``LOW * aging_interval``.

The point of the exercise is that switching policy requires editing
configuration only -- no code change::

    scheduler:
      policy: "fifo"          # <-- flip this to "priority"
      fifo:     {batch_interval: 0.01}
      priority: {aging_interval: 5, default_priority: "normal"}

Usage
-----
    python scripts/demo_priority_scheduling.py                  # both policies
    python scripts/demo_priority_scheduling.py --policy priority
    python scripts/demo_priority_scheduling.py --scenario starvation
    python scripts/demo_priority_scheduling.py --config aios/config/config.yaml

How the simulation works
------------------------
No model backend is needed. A :class:`SimulatedClock` stands in for
``LLMAdapter``: every dispatch advances a *simulated* clock by the request's
declared service time and then admits whatever has "arrived" by then. Because
the adapter is called from the scheduler's own thread, the run is deterministic:
the same configuration always produces the same chart.

Honest limitations (worth stating in a review):

* **No preemption.** A request that is already executing cannot be interrupted,
  so an arriving high-priority request waits for the in-flight call. This is
  real AIOS behaviour, not a simulation artifact -- the kernel drains its queue
  between dispatches.
* **Arrivals are noticed at dispatch boundaries**, because the kernel only reads
  the request queue between dispatches.
* **A single model backend**, so LLM calls are modelled as sequential.
* **Round robin's time slicing is not modelled.** ``RRScheduler`` stamps
  ``time_slice`` on each syscall and dispatches one syscall per round, so it is
  compared here as "one syscall at a time, in arrival order". AIOS only acts on
  that slice when ``use_context_manager`` is enabled -- the adapter consults
  ``Syscall.time_limit`` solely in its context-manager branch, and a suspended
  generation is resumed by ``SyscallExecutor`` re-submitting the request. This
  harness drives the scheduler directly, so it models one-syscall-per-round and
  nothing more. Round robin therefore shows the same ordering as FIFO in these
  workloads, which is itself the point: both built-in policies are urgency-blind.
* **Times are simulated seconds; aging counts dispatch rounds.** The two units
  are deliberately not the same: aging must not depend on how long a model call
  happens to take.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from dataclasses import dataclass
from math import ceil
from queue import Queue
from threading import Event
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# Ensure the project root is on the path so aios
# can be imported when running from scripts/
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from aios.scheduler.priority_policy import PriorityLevel
from aios.scheduler.registry import (
    POLICY_FIFO,
    POLICY_PRIORITY,
    POLICY_ROUND_ROBIN,
    create_scheduler,
    policy_options,
    resolve_policy_name,
)

#: Policies this harness can drive. See the module docstring for round_robin.
DEMO_POLICIES: Tuple[str, ...] = (
    POLICY_FIFO,
    POLICY_ROUND_ROBIN,
    POLICY_PRIORITY,
)

#: The configuration the demo starts from -- the same keys as config.yaml.
DEFAULT_CONFIG: Dict[str, Any] = {
    # "console" (not "file") because AIOS builds log file names from a timestamp
    # containing colons, which Windows rejects. The demo replaces the logger
    # with a silent one anyway; see _NullLogger.
    "log_mode": "console",
    "policy": POLICY_FIFO,
    "fifo": {"batch_interval": 0.01},
    "round_robin": {"time_slice": 1.0},
    "priority": {"aging_interval": 5, "default_priority": "normal"},
}

#: An aging interval large enough that no request ages within a run.
AGING_OFF = 10 ** 6


# ======================================================================
# Workload model
# ======================================================================
@dataclass(frozen=True)
class Work:
    """One LLM call an agent wants to make."""

    agent: str
    priority: str
    arrival: float
    service: float


@dataclass
class Dispatch:
    """A recorded dispatch, in simulated time."""

    agent: str
    priority: str
    arrival: float
    start: float
    end: float
    round_index: int
    admitted_round: int

    @property
    def wait(self) -> float:
        """Simulated seconds from arrival to dispatch."""
        return self.start - self.arrival

    @property
    def rounds_waited(self) -> int:
        """Dispatch rounds this request was ready before being dispatched."""
        return self.round_index - self.admitted_round


class DemoSyscall:
    """Minimal stand-in for ``aios.syscall.Syscall`` carrying its simulated cost."""

    def __init__(self, work: Work, admitted_round: int):
        self.work = work
        self.admitted_round = admitted_round
        self.agent_name = work.agent
        self.priority = work.priority
        self.status: Optional[str] = None
        self.response: Any = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.event = Event()

    def get_priority(self):
        return self.priority

    def set_priority(self, value):
        self.priority = value

    def set_status(self, value):
        self.status = value

    def get_status(self):
        return self.status

    def set_start_time(self, value):
        self.start_time = value

    def set_end_time(self, value):
        self.end_time = value

    def set_response(self, value):
        self.response = value

    def set_time_limit(self, value):
        self.start_time = value

    def get_pid(self):
        return id(self)

    def __repr__(self) -> str:
        return f"DemoSyscall({self.agent_name}, {self.priority})"


class WorkProbe:
    """Lets the clock ask the scheduler whether it still holds ready work.

    A scheduler keeps its own ready set, so the request queue alone cannot tell
    the harness whether the system is idle. ``PriorityScheduler`` exposes
    ``ready_snapshot``; policies without one (FIFO dispatches a drained batch
    synchronously) simply report no hidden work.
    """

    scheduler: Any = None

    def __call__(self) -> bool:
        if self.scheduler is None:
            return False
        snapshot = getattr(self.scheduler, "ready_snapshot", None)
        return bool(snapshot()) if callable(snapshot) else False


class SimulatedClock:
    """Stands in for ``LLMAdapter``: advances simulated time on each dispatch.

    Called from the scheduler's own thread, so every field here is touched by a
    single thread and the run is deterministic.
    """

    def __init__(
        self,
        workload: Sequence[Work],
        queue: Queue,
        has_work: Optional[Callable[[], bool]] = None,
    ):
        # Stable sort: requests that "arrive" at the same instant keep the order
        # they were declared in, which keeps runs reproducible.
        self._pending: List[Work] = sorted(workload, key=lambda work: work.arrival)
        self._queue = queue
        self._has_work = has_work or (lambda: False)
        self._batch_remaining = 0
        self.busy = False
        self.now = 0.0
        self.round = 0
        self.dispatches: List[Dispatch] = []

    # -- adapter interface ---------------------------------------------
    def execute_llm_syscalls(self, llm_syscalls) -> None:
        """Called by the scheduler; one simulated LLM call per syscall."""
        batch = list(llm_syscalls)
        for index, syscall in enumerate(batch):
            # FIFO hands over a whole batch; the rest of it is work the
            # scheduler still has, even though its queue is empty.
            self._batch_remaining = len(batch) - index - 1
            self._dispatch_one(syscall)
        self._batch_remaining = 0

    # -- simulation ----------------------------------------------------
    def prime(self) -> None:
        """Admit everything that has arrived at t=0 before the scheduler starts."""
        self._admit_due()

    def _dispatch_one(self, syscall: DemoSyscall) -> None:
        work = syscall.work
        self.busy = True
        start = self.now
        end = start + work.service
        self.dispatches.append(
            Dispatch(
                agent=work.agent,
                priority=work.priority,
                arrival=work.arrival,
                start=start,
                end=end,
                round_index=self.round,
                admitted_round=syscall.admitted_round,
            )
        )
        self.round += 1
        self.now = end

        self._admit_due()
        if self._is_idle() and self._pending:
            # Nothing is runnable: skip the idle gap to the next arrival, as a
            # real kernel would simply wait with an empty queue.
            self.now = self._pending[0].arrival
            self._admit_due()
        self.busy = False

        # Complete the syscall lifecycle, as the real adapter would.
        syscall.set_status("done")
        syscall.set_response(f"simulated response for {work.agent}")
        syscall.set_end_time(self.now)
        syscall.event.set()

    def _is_idle(self) -> bool:
        return (
            self._batch_remaining == 0
            and not self.busy
            and self._queue.empty()
            and not self._has_work()
        )

    def _admit_due(self) -> None:
        while self._pending and self._pending[0].arrival <= self.now + 1e-9:
            self._queue.put(DemoSyscall(self._pending.pop(0), self.round))

    @property
    def remaining(self) -> int:
        return len(self._pending) + self._queue.qsize()


class TimingPolicy:
    """Wraps a policy to measure the cost of the scheduling decision itself.

    This is the scheduler overhead an operating systems review asks about: the
    time spent *deciding*, measured inside a real run and excluding the
    simulated model latency.
    """

    def __init__(self, inner: Any):
        self.inner = inner
        self.calls = 0
        self.nanoseconds = 0
        self.max_ready = 0

    def select(self, ready: Sequence[Any], now_tick: int):
        self.max_ready = max(self.max_ready, len(ready))
        start = time.perf_counter_ns()
        chosen = self.inner.select(ready, now_tick)
        self.nanoseconds += time.perf_counter_ns() - start
        self.calls += 1
        return chosen

    def __getattr__(self, name: str):
        return getattr(self.inner, name)

    @property
    def mean_microseconds(self) -> float:
        return (self.nanoseconds / self.calls / 1000.0) if self.calls else 0.0

    @property
    def total_microseconds(self) -> float:
        return self.nanoseconds / 1000.0


# ======================================================================
# Scenarios
# ======================================================================
@dataclass
class Scenario:
    key: str
    title: str
    notes: List[str]
    workload: List[Work]


def scenario_interactive() -> Scenario:
    """A chat request arriving while a long batch job holds the LLM."""
    workload: List[Work] = []
    # A batch job: all ten steps are queued at t=0 and run back to back, which is
    # what creates the head-of-line blocking that an interactive request meets.
    for _ in range(10):
        workload.append(Work("report_agent", "low", arrival=0.0, service=5.0))
    # One short, urgent interactive request arrives mid-job.
    workload.append(Work("chat_agent", "high", arrival=21.0, service=1.0))
    # A normal-priority agent that shows up while the batch job is still running.
    for step in range(3):
        workload.append(
            Work("metrics_agent", "normal", arrival=49.0 + step * 2.0, service=2.0)
        )
    return Scenario(
        key="interactive",
        title="Interactive request during a long batch job",
        notes=[
            "report_agent  (low)    : 10 x 5.0s queued at t=0 (a 50s batch job)",
            "chat_agent    (high)   :  1 x 1.0s arriving at t=21  <-- the 1s request",
            "metrics_agent (normal) :  3 x 2.0s arriving at t=49, 51, 53",
            "",
            "Every arrival is due before the machine would otherwise go idle, so all",
            "policies process exactly 57s of service and only the ORDER changes.",
            "Under FIFO the 1s chat waits for the whole batch job. Priority serves it",
            "as soon as the in-flight call returns -- AIOS cannot preempt a running",
            "call, so the floor is one service time, not zero.",
        ],
        workload=workload,
    )


def scenario_starvation() -> Scenario:
    """A continuous flood of high-priority work against one low-priority request."""
    workload = [Work("low_agent", "low", arrival=0.0, service=1.0)]
    for _ in range(40):
        workload.append(Work("high_agent", "high", arrival=0.0, service=1.0))
    return Scenario(
        key="starvation",
        title="Starvation test: 40 high-priority requests against one low-priority request",
        notes=[
            "low_agent  (low)  :  1 x 1.0s, arrives at t=0",
            "high_agent (high) : 40 x 1.0s, all arrive at t=0",
            "",
            "Naive priority ordering would never dispatch low_agent. Aging must",
            "bound its wait at LOW x aging_interval = 2 x aging_interval rounds.",
            "FIFO is the opposite failure: it serves low_agent first and is blind",
            "to the fact that 40 urgent requests are waiting.",
        ],
        workload=workload,
    )


SCENARIOS: Dict[str, Callable[[], Scenario]] = {
    "interactive": scenario_interactive,
    "starvation": scenario_starvation,
}


# ======================================================================
# Running a policy
# ======================================================================
class _NullLogger:
    """Swallows the scheduler's per-dispatch log so the charts stay readable.

    The real logger is kept when ``--verbose`` is given. Note that AIOS's
    ``log_mode: file`` cannot be used on Windows at all: ``SchedulerLogger``
    builds the file name from a timestamp containing colons, which Windows
    rejects, so every dispatch would fail.
    """

    log_file: Optional[str] = None

    def log(self, content: str, level: str) -> None:
        return None


@dataclass
class RunResult:
    policy: str
    label: str
    options: Dict[str, Any]
    dispatches: List[Dispatch]
    timing: Optional[TimingPolicy] = None
    wall_seconds: float = 0.0
    log_file: Optional[str] = None
    completed: bool = True

    @property
    def makespan(self) -> float:
        return max((d.end for d in self.dispatches), default=0.0)

    @property
    def busy_time(self) -> float:
        return sum(d.end - d.start for d in self.dispatches)

    @property
    def idle_time(self) -> float:
        return max(0.0, self.makespan - self.busy_time)

    def by_agent(self) -> Dict[str, List[Dispatch]]:
        grouped: Dict[str, List[Dispatch]] = {}
        for dispatch in self.dispatches:
            grouped.setdefault(dispatch.agent, []).append(dispatch)
        return grouped


def bounded_getter(queue: Queue, timeout: float = 0.05):
    """Mimic ``aios/hooks/stores/queue.py``: a bounded blocking get."""

    def getter():
        return queue.get(block=True, timeout=timeout)

    return getter


def run_policy(
    config: Dict[str, Any],
    workload: Sequence[Work],
    label: Optional[str] = None,
    timeout: float = 60.0,
    verbose: bool = False,
) -> RunResult:
    """Run one workload through whichever policy ``config`` selects."""
    # The policy is read from configuration, exactly as the kernel does it.
    policy = resolve_policy_name(config)
    options = policy_options(config, policy)

    queue: Queue = Queue()
    # Idle queues so that start()/stop() can run all four processor threads.
    idle_queues = [Queue() for _ in range(3)]
    probe = WorkProbe()
    clock = SimulatedClock(workload, queue, has_work=probe)

    scheduler = create_scheduler(
        policy,
        llm=clock,
        memory_manager=None,
        storage_manager=None,
        tool_manager=None,
        log_mode=config.get("log_mode", "console"),
        get_llm_syscall=bounded_getter(queue),
        get_memory_syscall=bounded_getter(idle_queues[0]),
        get_storage_syscall=bounded_getter(idle_queues[1]),
        get_tool_syscall=bounded_getter(idle_queues[2]),
        **options,
    )
    probe.scheduler = scheduler

    if not verbose:
        scheduler.logger = _NullLogger()

    timing = None
    if hasattr(scheduler, "policy"):
        timing = TimingPolicy(scheduler.policy)
        scheduler.policy = timing

    log_file = getattr(scheduler.logger, "log_file", None)

    clock.prime()
    started = time.perf_counter()
    scheduler.start()
    try:
        deadline = started + timeout
        while len(clock.dispatches) < len(workload) and time.perf_counter() < deadline:
            time.sleep(0.01)
    finally:
        scheduler.stop()

    completed = len(clock.dispatches) >= len(workload)
    if not completed:
        print(
            f"  WARNING: only {len(clock.dispatches)}/{len(workload)} requests were "
            f"dispatched in {timeout:.0f}s. The workload probably has an idle gap "
            f"that a non-preemptive policy cannot cross."
        )

    return RunResult(
        policy=policy,
        label=label or policy,
        options=options,
        dispatches=clock.dispatches,
        timing=timing,
        wall_seconds=time.perf_counter() - started,
        log_file=log_file,
        completed=completed,
    )


# ======================================================================
# Rendering
# ======================================================================
def format_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    columns = [list(map(str, column)) for column in zip(*([headers] + list(rows)))]
    widths = [max(len(cell) for cell in column) for column in columns]
    lines = [
        "  " + "  ".join(cell.ljust(width) for cell, width in zip(headers, widths))
    ]
    lines.append("  " + "  ".join("-" * width for width in widths))
    for row in rows:
        lines.append(
            "  "
            + "  ".join(
                str(cell).ljust(width) for cell, width in zip(row, widths)
            )
        )
    return "\n".join(lines)


def time_axis(total: float, width: int, ticks: int = 6) -> str:
    axis = [" "] * width
    for index in range(ticks + 1):
        value = total * index / ticks
        label = f"{value:g}"
        cell = int(round(value / total * (width - 1))) if total else 0
        cell = max(0, min(cell, width - len(label)))
        if any(char != " " for char in axis[max(0, cell - 1) : cell + len(label) + 1]):
            continue
        for offset, char in enumerate(label):
            axis[cell + offset] = char
    return "".join(axis) + " (simulated seconds)"


def render_gantt(result: RunResult, width: int = 74) -> str:
    """ASCII Gantt chart: one row per agent, columns spanning the makespan."""
    if not result.dispatches:
        return "  (nothing was dispatched)"

    total = result.makespan or 1.0
    agents: List[str] = []
    for dispatch in result.dispatches:
        if dispatch.agent not in agents:
            agents.append(dispatch.agent)

    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    symbols = {agent: alphabet[index % len(alphabet)] for index, agent in enumerate(agents)}
    grid = {agent: ["."] * width for agent in agents}

    for dispatch in result.dispatches:
        first = min(int(dispatch.start / total * width), width - 1)
        last = max(first + 1, ceil(dispatch.end / total * width))
        for cell in range(first, min(last, width)):
            grid[dispatch.agent][cell] = symbols[dispatch.agent]

    lines = ["      " + time_axis(total, width)]
    for agent in agents:
        priority = result.by_agent()[agent][0].priority
        lines.append(
            f"  {symbols[agent]}  {agent:<14} {priority:<6} |{''.join(grid[agent])}|"
        )
    lines.append("      " + " " * 25 + "(.) idle    (A,B,C...) which agent held the LLM")
    return "\n".join(lines)


def agent_stats(result: RunResult) -> List[List[Any]]:
    rows: List[List[Any]] = []
    for agent, dispatches in result.by_agent().items():
        waits = [dispatch.wait for dispatch in dispatches]
        response = min(dispatch.start for dispatch in dispatches) - min(
            dispatch.arrival for dispatch in dispatches
        )
        rows.append(
            [
                agent,
                dispatches[0].priority,
                len(dispatches),
                f"{sum(d.end - d.start for d in dispatches):.1f}",
                f"{response:.1f}",
                f"{sum(waits) / len(waits):.1f}",
                f"{max(waits):.1f}",
                f"{max(d.rounds_waited for d in dispatches)}",
            ]
        )
    return rows


AGENT_HEADERS = [
    "agent",
    "priority",
    "reqs",
    "service(s)",
    "response(s)",
    "mean wait(s)",
    "max wait(s)",
    "max wait(rounds)",
]


def render_run(result: RunResult, width: int = 74) -> str:
    label = result.label
    if result.label != result.policy:
        label = f"{result.policy} / {result.label}"

    header = f"--- policy: {label} " + "-" * max(0, 60 - len(label))
    if not result.dispatches:
        return f"{header}\n  (nothing was dispatched)"

    lines = [
        header,
        "  resolved from config: "
        f"policy={result.policy!r}  options={result.options or '{}'}",
        "",
        render_gantt(result, width),
        "",
        format_table(AGENT_HEADERS, agent_stats(result)),
        "",
    ]

    waits = [dispatch.wait for dispatch in result.dispatches]
    lines.append(
        f"  makespan={result.makespan:.1f}s  busy={result.busy_time:.1f}s  "
        f"idle={result.idle_time:.1f}s  throughput="
        f"{len(result.dispatches) / result.makespan:.2f} req/s"
    )
    lines.append(
        f"  mean wait={sum(waits) / len(waits):.1f}s  "
        f"max wait={max(waits):.1f}s  dispatches={len(result.dispatches)}"
    )
    if result.timing is not None:
        lines.append(
            f"  scheduler overhead: {result.timing.calls} decisions, "
            f"{result.timing.mean_microseconds:.1f} us mean "
            f"({result.timing.total_microseconds:.0f} us total), "
            f"largest ready set={result.timing.max_ready}"
        )
    else:
        reason = (
            "dispatches a whole batch at once, so there is no per-request decision"
            if result.policy == POLICY_FIFO
            else "takes the head of the queue, so there is no decision step to time"
        )
        lines.append(f"  scheduler overhead: n/a - this policy {reason}")
    return "\n".join(lines)


# ======================================================================
# Reporting
# ======================================================================
def comparison_rows(results: Sequence[RunResult], agents: Sequence[str]) -> List[List[Any]]:
    rows: List[List[Any]] = []
    for result in results:
        if not result.dispatches:
            rows.append([result.label] + ["-"] * (len(agents) + 3))
            continue
        grouped = result.by_agent()
        row: List[Any] = [result.label]
        for agent in agents:
            if agent not in grouped:
                row.append("-")
                continue
            response = min(d.start for d in grouped[agent]) - min(
                d.arrival for d in grouped[agent]
            )
            row.append(f"{response:.1f}")
        waits = [dispatch.wait for dispatch in result.dispatches]
        row.append(f"{sum(waits) / len(waits):.1f}")
        row.append(f"{max(waits):.1f}")
        row.append(f"{len(result.dispatches) / result.makespan:.2f}")
        rows.append(row)
    return rows


def report_scenario(
    scenario: Scenario,
    config: Dict[str, Any],
    width: int,
    verbose: bool = False,
    timeout: float = 60.0,
) -> List[RunResult]:
    print("=" * 78)
    print(f"SCENARIO: {scenario.title}")
    print("=" * 78)
    for note in scenario.notes:
        print(f"  {note}" if note else "")
    print()

    results: List[RunResult] = []
    for policy in DEMO_POLICIES:
        run_config = dict(config)
        run_config["policy"] = policy
        result = run_policy(
            run_config, scenario.workload, verbose=verbose, timeout=timeout
        )
        results.append(result)
        print(render_run(result, width))
        print()

    agents = list(dict.fromkeys(work.agent for work in scenario.workload))
    headers = ["policy"] + [f"{agent} response(s)" for agent in agents] + [
        "mean wait(s)",
        "max wait(s)",
        "throughput",
    ]
    print("COMPARISON (response = time from arrival to first dispatch)")
    print(format_table(headers, comparison_rows(results, agents)))
    print()
    return results


def report_starvation_bound(
    scenario: Scenario,
    config: Dict[str, Any],
    verbose: bool = False,
    timeout: float = 60.0,
) -> None:
    """Show that aging is what makes the priority policy starvation-free."""
    aging_interval = config.get("priority", {}).get("aging_interval", 5)
    bound = int(PriorityLevel.LOW) * aging_interval

    runs: List[Tuple[str, RunResult]] = []
    for label, interval in (("aging on", aging_interval), ("aging off", AGING_OFF)):
        run_config = dict(config)
        run_config["policy"] = POLICY_PRIORITY
        run_config["priority"] = dict(
            config.get("priority", {}), aging_interval=interval
        )
        runs.append(
            (
                label,
                run_policy(
                    run_config,
                    scenario.workload,
                    label=label,
                    verbose=verbose,
                    timeout=timeout,
                ),
            )
        )

    print("=" * 78)
    print("STARVATION ANALYSIS (low-priority request against a flood of high-priority work)")
    print("=" * 78)
    print(f"  aging_interval                 : {aging_interval} rounds")
    print(f"  starvation bound (LOW x interval): {bound} rounds")
    print()

    verdict = "INCONCLUSIVE"
    for label, result in runs:
        low = result.by_agent().get("low_agent")
        if not low:
            print(f"  {label:<10}: low_agent was never dispatched  <-- STARVED")
            continue
        waited = low[0].rounds_waited
        if label == "aging on":
            verdict = "PASS" if waited <= bound else "FAIL"
            print(
                f"  {label:<10}: low_agent dispatched after {waited} rounds "
                f"(waited {low[0].wait:.1f}s)  [{verdict} - within the bound]"
            )
        else:
            print(
                f"  {label:<10}: low_agent dispatched after {waited} rounds "
                f"(waited {low[0].wait:.1f}s)"
            )
    print()
    print(
        "  Every high-priority request that arrives later loses the tie against a\n"
        "  request that has aged to the top level, so the low-priority request's wait\n"
        "  is bounded by the aging horizon. Without aging the wait grows with the\n"
        "  length of the high-priority stream, which is unbounded starvation."
    )
    print()


# ======================================================================
# Entry point
# ======================================================================
def load_config(path: Optional[str]) -> Tuple[Dict[str, Any], str]:
    config = {key: (dict(value) if isinstance(value, dict) else value)
              for key, value in DEFAULT_CONFIG.items()}
    if not path:
        return config, "built-in defaults"

    import yaml

    with open(path, "r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    section = loaded.get("scheduler") or {}
    if not section:
        return config, f"{path} (no scheduler section; using defaults)"
    for key, value in section.items():
        config[key] = value
    return config, path


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare AIOS scheduling policies with a Gantt chart.",
    )
    parser.add_argument(
        "--policy",
        choices=list(DEMO_POLICIES),
        help="restrict the comparison to one policy (the default is both)",
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS) + ["all"],
        default="all",
        help="which workload to run (default: all)",
    )
    parser.add_argument(
        "--aging-interval",
        type=int,
        help="override scheduler.priority.aging_interval",
    )
    parser.add_argument(
        "--config",
        help="read the scheduler section from this config.yaml",
    )
    parser.add_argument("--width", type=int, default=74, help="Gantt chart width")
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="seconds to wait for one run to finish (default: 60)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="keep the scheduler's per-dispatch log lines",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    # The scheduler modules log at INFO; keep the demo output readable.
    logging.disable(logging.INFO)

    global DEMO_POLICIES
    if args.policy:
        DEMO_POLICIES = (args.policy,)

    config, source = load_config(args.config)
    if args.aging_interval is not None:
        config["priority"] = dict(
            config.get("priority", {}), aging_interval=args.aging_interval
        )
    if args.policy:
        config["policy"] = args.policy

    print()
    print("AIOS scheduling demo - policy selected by name from configuration")
    print(f"  config source: {source}")
    print("  scheduler section used by this run:")
    for key in ("policy", "fifo", "round_robin", "priority"):
        if key in config:
            marker = "   <-- flip this to switch policy" if key == "policy" else ""
            print(f"      scheduler.{key}: {config[key]}{marker}")
    print(f"  policies compared here: {', '.join(DEMO_POLICIES)}")
    print()

    scenario_keys = list(SCENARIOS) if args.scenario == "all" else [args.scenario]
    for key in scenario_keys:
        scenario = SCENARIOS[key]()
        results = report_scenario(
            scenario,
            config,
            args.width,
            verbose=args.verbose,
            timeout=args.timeout,
        )
        if key == "starvation":
            report_starvation_bound(
                scenario, config, verbose=args.verbose, timeout=args.timeout
            )
        for result in results:
            if result.log_file:
                print(f"  scheduler log: {result.log_file}")
                break

    print("=" * 78)
    print("Done. Flip scheduler.policy in config.yaml and re-run to switch policies.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
