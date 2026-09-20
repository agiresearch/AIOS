# Design: Priority-based Agent-level Scheduling for AIOS

| | |
|---|---|
| **Status** | Draft — design review welcome |
| **Related issue** | #127 (*AIOS Semantic Scheduling* → *Priority-based Agent-level Scheduling*) |
| **Tracking issue** | `#554 ` |
| **Authors** | Group of 5 — university operating systems course project |
| **Scope** | `aios/scheduler/`, `aios/hooks/types/`, `runtime/launch.py`, `aios/config/`, `tests/` |

---

## 1. Summary

AIOS is an agent operating system whose central responsibility is deciding which agent gets
the LLM next. Today that decision is made by only two policies — first-come-first-served
(`FIFOScheduler`) and round-robin (`RRScheduler`) — and it cannot express importance or
fairness.

This document proposes an **opt-in, non-breaking** scheduling feature that adds:

1. **Agent priority levels** that influence dispatch order.
2. **Weighted fair-share** so no agent can monopolize LLM capacity.
3. **Aging**, which guarantees a low-priority agent still runs within a bounded wait.
4. **A policy registry**, so the active policy is chosen by name from configuration.
5. **Per-agent accounting and observability**, without which none of the above can be
   evaluated.

Existing behaviour is unchanged: `FIFOScheduler` and `RRScheduler` are left untouched, the
new policies are **off by default**, and there are **no new third-party dependencies**.

---

## 2. Motivation

The scheduler is the reason an "agent operating system" exists, but the current
implementation cannot handle three situations that arise in normal use:

- **Head-of-line blocking.** One long-running agent blocks a short interactive one
  completely. A chat request waits behind a multi-minute report generation.
- **Noisy neighbours.** When several agents or users share one AIOS deployment, nothing
  bounds a heavy agent's share of LLM capacity. There are no weights, shares, or usage
  counters anywhere in the codebase.
- **No protection against starvation.** With no notion of priority, there is nothing that
  could starve — but there is also nothing that lets an urgent agent be served first. Adding
  priority *without* aging would introduce starvation, which is why aging is part of this
  design rather than a follow-up.

The gap is also publicly acknowledged: *Priority-based Agent-level Scheduling for AIOS* has
been listed under *AIOS Semantic Scheduling* in roadmap issue #127 since May 2024,
unassigned and unimplemented.

---

## 3. Current state in AIOS (verified)

| Item | Current state |
|---|---|
| `aios/scheduler/` | `__init__.py`, `base.py`, `fifo_scheduler.py`, `rr_scheduler.py` — two policies, no priority, no fairness |
| Policy selection | Determined internally by the unrelated `use_context_manager` flag in `runtime/launch.py` |
| `priority` field | `aios/syscall/__init__.py` defines `self.priority`, `set_priority()`, `get_priority()` — **no call sites anywhere in the repository** |
| Scheduler settings | `SchedulerParams` (`aios/hooks/types/scheduler.py`) accepts only the four managers, `log_mode` and four queue-reader callbacks |
| `scheduler:` config | `aios/config/config.yaml.example` contains only `log_mode` |
| Accounting | None — no per-agent usage tracking |
| Scheduler metrics | `SyscallExecutor._execute_syscall` computes waiting/turnaround times, but returns on the success path before recording them, so the recorded lists are always empty |
| Scheduler tests | None — `tests/` contains no scheduler tests |

The `priority` field and the config surface were evidently anticipated by the existing
design; the policy itself was never implemented.

*This table describes `main` before the change — it is what motivates the work, not a
description of this branch. See §5.2 for what is implemented here.*

---

## 4. Goals and non-goals

### Goals

- An agent can be labelled `high` / `normal` / `low`, and this affects dispatch order.
- Each agent can be given a weight guaranteeing a proportional share of dispatched work.
- A waiting request is guaranteed to be dispatched within a bounded number of scheduling
  ticks, regardless of how many high-priority requests arrive.
- The active policy is selectable by name in `config.yaml`.
- Per-agent usage, waiting time, turnaround time, and a fairness score are observable.
- The policy logic is unit-testable in isolation, without a live LLM backend.

### Non-goals

- Replacing or modifying `FIFOScheduler` / `RRScheduler`, or changing default behaviour.
- Preemptive interruption of an in-flight LLM call. This design schedules **which request
  is dispatched next**; it does not interrupt running generations. (On LLM backends, an
  interrupted generation is not free to resume, so preemption is deliberately a separate
  design problem.)
- Admission control / bounded queues. Complementary work, out of scope here.
- Changes to the agent SDK. The `priority` field already exists on every request; this
  design intends to *consume* it, not extend the API.

---

## 5. Design

### 5.1 Architecture

```
                       config.yaml  (scheduler.policy = "priority")
                            │
                            ▼
                   SchedulerRegistry ──── name → class
                            │
                            ▼
  Agent ──► SyscallExecutor ──► request queues ──► SelectedPolicy  (BaseScheduler subclass)
                                                       │
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                                  AgentLedger               PolicyDecision
                              (per-agent usage,           (which syscall
                               priority, weight)           is dispatched next)
                                          │                         │
                                          └────────────┬────────────┘
                                                       ▼
                                            LLMAdapter.execute_llm_syscalls(batch)
                                                       │
                                                       ▼
                                      MetricsCollector ──► per-agent stats + fairness score
```

The three existing schedulers keep their shape. A new policy is a `BaseScheduler` subclass
that implements the four `process_*_requests` methods plus `start` / `stop`, and — instead
of draining the queue in arrival order — builds a batch using its policy decision function.

### 5.2 Components

Sections below are marked **done** when they are implemented and tested in the current
branch, and **planned** when they are follow-up work from the task checklist.

**`SchedulerRegistry`** (`aios/scheduler/registry.py`, new) — **done**
Maps a policy name to its class: `fifo` (alias `fcfs`), `round_robin`, `priority`. Adding a
future policy becomes a one-line registration. This is the policy/mechanism split: the
dispatch machinery stays fixed while the rule becomes pluggable.

The registry is also the only place that knows which option keys each policy accepts, so an
option belonging to a different policy is ignored rather than passed to a constructor that
cannot accept it. An unknown policy name raises at start-up rather than silently falling
back to FIFO — an operator who believes a policy is active when it is not is worse off than
one whose kernel refuses to start.

**`PriorityPolicy`** (`aios/scheduler/priority_policy.py`, new) — **done**
The decision logic only: levels, the aging formula, the selection rule and the starvation
bound. It imports nothing from AIOS, so it can be unit-tested and benchmarked without
`cerebrum`, a model backend or a running server, and a future `aios-rs` port can mirror it
without inheriting the Python kernel's dependency graph.

**`PriorityScheduler`** (`aios/scheduler/priority_scheduler.py`, new) — **done**
The thin adapter that feeds real `aios.syscall.Syscall` objects into the policy and connects
it to the kernel's threads, queues and syscall lifecycle.

**`SchedulerManager`** (`aios/scheduler/manager.py`, new) — **done**
Owns the live scheduler, so the policy can change while the kernel is running instead of
only at start-up. All four request queues are module-level globals, which is what makes a
swap possible: a new scheduler instance reads the same queues. What is *not* shared is a
scheduler's own state — a `PriorityScheduler` holds requests it has already accepted in a
ready set, and each of those is a thread blocked on `syscall.join()`. So the swap is
ordered: construct the new scheduler first (a bad policy name or option is then rejected
while the running one is untouched), stop the old one and let its threads exit, hand any
accepted-but-undispatched requests back to the request queue, then start the new one.

This is the part of the design most likely to be got wrong, so it has the most pointed
test: `test_switch_requeues_requests_that_were_accepted_but_not_dispatched`.

**`AgentLedger`** (`aios/scheduler/accounting.py`, planned)
The per-agent record that makes fairness possible. Agents are identified by
`syscall.agent_name`, which AIOS already uses as the agent identity throughout the syscall
path.

```python
@dataclass
class AgentRecord:
    name: str
    priority: int          # 0 = high, 1 = normal, 2 = low
    weight: int            # fair-share weight, default 1
    dispatched: int = 0    # LLM dispatches charged to this agent
    wait_ticks: int = 0    # ticks spent waiting since last dispatch
    pass_value: float = 0.0  # virtual time, used by fair-share
    waiting_since: float | None = None
    total_wait: float = 0.0
    total_turnaround: float = 0.0
```

The ledger is guarded by a single lock; it is small, and fairness is impossible without a
consistent view of it.

**`MetricsCollector`** (`aios/utils/metrics.py`, planned)
Aggregates per-agent waiting/turnaround and computes a **Jain fairness index** over
normalized dispatches:

```
J = (Σ xᵢ)² / (n · Σ xᵢ²)        xᵢ = dispatched_i / weight_i
```

`J = 1` means perfectly proportional; lower means a heavier share went to some agents.

### 5.3 Policies

#### `priority` — priority with aging — **done**

Each queued request carries a base level from `priority` (`high=0, normal=1, low=2`).
Levels are normalised from whatever the caller supplied, so `PriorityLevel.HIGH`,
`"high"`, `"URGENT"` and `0` all resolve to HIGH, an unrecognised value falls back to
`default_priority`, and an out-of-range integer is clamped rather than rejected — a
malformed priority from a caller must not take the kernel down.

```
effective_level(r) = max(0, r.base_level - r.wait_ticks // aging_interval)
select = the queued request minimising (effective_level, arrival_time)
```

**Starvation bound.** A request whose base level is `L` escalates one level every
`aging_interval` ticks, so it reaches the top level within

```
(L - 0) × aging_interval  ticks        # 2 × aging_interval for a low-priority request
```

Ticks are scheduling rounds, not wall-clock seconds, which keeps the bound independent of
how slow an individual LLM call happens to be. This bound is a testable property, and the
test suite asserts it.

#### `fair_share` — weighted fair queueing with virtual time (stride scheduling) — **planned**

Standard stride scheduling: agent `i` has weight `wᵢ`; each dispatch advances its virtual
time by the inverse of its weight, and the agent with the smallest virtual time runs next.

```
stride_i  = STRIDE_BASE / w_i
pass_i   += stride_i                 # on dispatch
select    = the queued request whose agent has the smallest pass_i
tie-break = priority level, then arrival_time
```

This guarantees proportional dispatch counts over time. A long-running heavy agent cannot
push a small-weight agent out: the small agent's `pass` stays low and it is chosen quickly.

**What is charged per dispatch.** v1 charges one unit per LLM syscall dispatched. This gives
accurate *call-count* fairness, which is the right model while different backends report
inconsistent token usage. Charging by tokens (via the response usage fields, where
available) is a natural v2 extension and is noted as such rather than half-implemented.

#### `fcfs` / `round_robin`

Retained exactly as they are today, re-exposed through the registry so that
`scheduler.policy` can select them by name. Their behaviour must not change — a regression
test asserts this.

### 5.4 Configuration

```yaml
scheduler:
  log_mode: "console"

  # Which agent gets the LLM next: fifo | round_robin | priority  (default: fifo)
  policy: "priority"

  # Options for one policy live under that policy's own key. Only the keys the
  # selected policy declares are read, so a stale key left over from another
  # policy cannot break start-up.
  fifo:
    batch_interval: 1.0        # seconds between scheduling rounds
  round_robin:
    time_slice: 1.0            # per-round time slice in seconds
  priority:
    aging_interval: 5          # dispatch rounds to gain one priority level
    default_priority: "normal" # used when a syscall carries no priority
```

`batch_interval` and `time_slice` were hard-coded constants before this change; they are now
read from configuration with their previous values as defaults, so the change is additive.

Naming no policy reproduces today's behaviour exactly: `round_robin` when
`llms.use_context_manager` is true (context switching is implemented by `RRScheduler`),
otherwise `fifo`. An existing `config.yaml` is therefore unaffected.

### 5.5 Compatibility and rollout

- New policies ship **opt-in**; `policy` defaults to `fcfs`.
- `FIFOScheduler` and `RRScheduler` are not modified.
- No new dependencies.
- Agent priority is read from the existing `Syscall.priority`; agents that never set it get
  `default_priority`.
- The new policies pass a **correctly-formed list** of syscalls to
  `LLMAdapter.execute_llm_syscalls(batch)`, which is the documented contract of that method.

### 5.6 Files

| File | Change |
|---|---|
| `aios/scheduler/registry.py` | **New** — policy name → class registry, config resolution |
| `aios/scheduler/priority_policy.py` | **New** — levels, aging, selection, starvation bound (no AIOS imports) |
| `aios/scheduler/priority_scheduler.py` | **New** — `PriorityScheduler`, the `BaseScheduler` adapter |
| `runtime/launch.py` | Select the policy from config via the registry; accept a per-request `priority` |
| `aios/syscall/syscall.py` | Carry the requested priority onto the syscall; arrival line shows it |
| `aios/config/config.yaml.example` | Document `policy` and the per-policy option blocks |
| `aios/scheduler/manager.py` | **New** — owns the live scheduler; runtime policy switching |
| `scripts/run_kernel.sh` | **New** — start the kernel with the environment it needs |
| `scripts/agent_tab.py` | **New** — one interactive agent tab per terminal |
| `aios/terminal/terminal.py` | **New** — the AIOS terminal, with per-tab `--priority` / `--model` / `--name` |
| `aios/terminal/tab_client.py` | **New** — backend → priority table, and the priority-carrying request payload |
| `runtime/run_terminal.py`, `scripts/run_terminal.py` | Thin entry points for the terminal above (they were near-identical copies) |
| `scripts/set_policy.py` | **New** — show or change the policy of a running kernel |
| `scripts/verify_policy.py` | **New** — check the reported policy is the one actually followed |
| `tests/modules/scheduler/` | **New** — unit, property and regression tests |
| `docs/scheduling/priority_scheduling.md` | **This document** |

Planned, not yet added: `aios/scheduler/accounting.py`, `aios/scheduler/fair_share_scheduler.py`,
`aios/utils/metrics.py`.

### 5.7 Getting a priority to the scheduler — **done**

The `priority` field has existed on every syscall from the start but never had a writer.
A client sets it by sending a top-level `priority` on `POST /query`:

1. `QueryRequest` accepts `priority` (`"high"` / `"normal"` / `"low"`, or a level).
2. The request handler attaches it to the query object as `query._request_priority` — a
   private attribute, the same mechanism the handler already uses for `user_id`, so the
   Cerebrum SDK query types stay unmodified.
3. `SyscallExecutor._execute_syscall` reads it back and calls `syscall.set_priority(...)` on
   each syscall it creates, which is what the policy reads via `syscall.get_priority()`.

A request that sends no priority leaves the field at `None` and the policy applies
`default_priority`, so the change is inert for every existing client and for the `fifo` and
`round_robin` policies.

### 5.8 Watching it live — **done**

**The allocation log.** Every scheduling decision prints one coloured line to the kernel
terminal, so the ready set can be seen being ordered in real time:

```
QUEUED   22:09:38  metrics_agent (normal)  queue=1
QUEUED   22:09:38  chat_agent (high)  queue=2
RUN      22:09:38  chat_agent (high)  waited 0.1s / 0 rounds  effective=high
DONE     22:09:39  chat_agent  took 1.1s  thread=3
READY    22:09:39  next -> metrics_agent(normal,waited 0)
```

The `READY` line is the policy made visible: the queue is printed already sorted, with the
aged level of every request, so a low-priority request climbing toward the front can be
watched.

`RUN` reports both wall-clock seconds and dispatch rounds. The two differ by design: rounds
drive aging, seconds are what a caller experiences. A request that spent 20 s behind a
single long generation has aged by zero rounds, which is correct — it was never passed
over, the backend was simply busy.

Arrival is printed by the syscall executor the moment a request is queued, before the
scheduler picks anything up, so a message typed in a tab is acknowledged immediately even
while the LLM is busy with another agent.

**The tab client.** `scripts/agent_tab.py` is one interactive agent per terminal. Open four
tabs with different `--priority` values, type a message in each, and the kernel terminal
shows which one was chosen and what it waited behind. `scripts/run_kernel.sh` starts the
kernel with the environment it needs.

AIOS's own terminal carries both as well. `aios/terminal/terminal.py` — entered through
`runtime/run_terminal.py` or `scripts/run_terminal.py` — takes `--name` for identity,
`--model` for the backend, and `--priority` for the level, defaulting the level to the
tab's backend: `ollama` high, `gemini` normal, `groq` low. `/priority`, `/model` and
`/name` change any of them without restarting the tab. Under `fifo` and `round_robin` the
`priority` field is accepted and ignored, which is what lets the same four tabs serve as
the comparison rather than as a special case.

**Changing policy without restarting.** Starting the kernel takes about 80 seconds, which
is too slow to compare policies on stage. The manager is exposed as:

```
GET  /core/scheduler          -> policy, class, options, dispatches so far, alternatives
POST /core/scheduler/policy   -> {"policy": "priority", "options": {"aging_interval": 3}}
```

and as `scripts/set_policy.py`. The `GET` also answers "which policy is actually running?"
for a kernel that is already up, which otherwise could only be inferred from start-up output
or from the class name prefixed onto each log line.

**Checking it is really in effect.** `scripts/verify_policy.py` separates the two things
that matter: *identity* comes from `GET /core/scheduler`, and *behaviour* comes from
submitting a LOW and a HIGH request at the same instant and seeing which reply lands first.
A policy can be selected while the priority is ignored, and the identity check alone would
not notice. The check also makes `fifo`'s limit concrete: it merges the pair into one model
call, so both finish together and priority makes no latency difference at all.

---

## 6. Testing

| Level | What it covers |
|---|---|
| Unit | Priority ordering; tie-breaks; ledger accounting; registry lookup and unknown-policy handling |
| Property (`hypothesis`) | **Starvation bound**: for arbitrary arrival sequences, a low-priority request is dispatched within `2 × aging_interval` ticks. Also: share adherence within tolerance for arbitrary weight vectors |
| Regression | `fcfs` behaves identically to `FIFOScheduler` on the same input trace |
| Metrics | Waiting/turnaround recorded for every completed syscall (today they are never recorded) |

The policy classes are written so they can be driven with synthetic request objects, so the
entire test suite runs without an LLM backend. This is deliberate: it keeps CI fast and makes
the guarantees checkable in isolation.

---

## 7. Evaluation plan

**Workloads.** Scripted agents with mixed task lengths (short interactive, medium, long
batch) and a Poisson arrival process; plus an overload regime where longer agents are
continuously present.

**Metrics.** Per-agent waiting and turnaround time; worst-case wait of the lowest-priority
agent (the starvation bound in practice); P50/P95/P99 turnaround of short agents; fairness
score; throughput (completed LLM syscalls per minute); scheduler decision overhead in
microseconds.

**Baselines.** `fcfs` as shipped (the default users actually run); `round_robin`; `priority`
**without** aging, to isolate what aging contributes; and an oracle lower bound.

**Expected result.** `priority` sharply reduces short-agent response time; `fair_share`
raises the fairness score while keeping short-agent latency low; the starvation bound holds
under overload; scheduler overhead is negligible relative to LLM call latency.

---

## 8. Open questions for the maintainers

1. Should each new policy be a separate `BaseScheduler` subclass (our assumption), or should
   the priority logic extend `FIFOScheduler`?
2. Preferred naming for the priority levels and config keys?
3. Any constraints from the `aios-rs` rewrite we should respect so the interface stays
   portable?
4. Is `Syscall.priority` intended to be set by the agent SDK, or derived by the kernel from
   agent configuration? We would like to use it as intended.

---

## 9. Prior work

Priority and multi-level scheduling for agent systems has been explored before — notably
*AgentRM: An OS-Inspired Resource Manager for LLM Agent Systems* (arXiv:2603.13110, 2026),
which uses a Multi-Level Feedback Queue. This design does **not** claim priority scheduling
as a novel concept. The contribution is a working, configurable implementation inside the
AIOS kernel consistent with roadmap #127, with an aging-based starvation guarantee and a
measured evaluation. MLFQ is a natural additional policy behind the same registry.

---

## 10. Task checklist

```
[x] Design document
[x] SchedulerRegistry + config plumbing
[x] Priority policy with aging
[x] Priority reaches the scheduler from a client request
[x] Tests: ordering, tie-breaking, aging progression
[x] Property test: starvation bound
[x] Command-line comparison harness (demo_priority_scheduling.py)
[x] Live end-to-end demo against a running kernel (agent_tab.py, run_terminal.py)
[x] Report the active policy of a running kernel (GET /core/scheduler)
[x] Change policy at runtime without dropping queued requests
[ ] AgentLedger
[ ] Fair-share policy (stride)
[ ] Property test: share adherence
[ ] Metrics + fairness score reporting
[ ] Regression test: fcfs unchanged
[ ] Evaluation write-up
```
