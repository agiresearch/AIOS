# scripts

## list_agents.py

List all agents available to use and install.

## run_kernel.sh

Start the AIOS kernel server. Sets the two environment variables the kernel
needs and that are easy to miss:

- `PYTHONUTF8` / `PYTHONIOENCODING` — `runtime/launch.py` prints emoji in its
  start-up messages. On a console encoded as cp1252 (the Windows default when
  output is redirected) those prints raise `UnicodeEncodeError`, which
  propagates out of `initialize_components()` and stops the kernel before it
  binds a port.
- `PYTHONPATH` — `aios` is not an installed package, so the project root has to
  be importable or `runtime/launch.py` fails with `ModuleNotFoundError`.

```bash
scripts/run_kernel.sh                          # DEBUG logging, historical output
AIOS_LOG_LEVEL=WARNING scripts/run_kernel.sh   # quiet: scheduler lines stand out
```

On PowerShell use `scripts\run_kernel.ps1`: same script, same two environment
variables, and it picks the project venv, because `python` on PATH is usually
the global interpreter and that one has no `litellm`.

The first start takes about 80 seconds while the kernel imports its components.
Whichever policy `scheduler.policy` names in `config.yaml` is printed when the
scheduler starts, so the log states the policy that is actually in effect.

## verify_policy.py

Check that the policy the kernel reports is the policy it is actually
following. Sends a LOW-priority and a HIGH-priority request at the same
instant and reports which reply arrives first.

```bash
python scripts/verify_policy.py
```

One command answers both halves of the question: `GET /core/scheduler` gives the
*identity*, and the race gives the *behaviour*. A policy could be selected while
the priority was ignored, which the identity check alone would not catch.

```
  policy     : priority
  scheduler  : PriorityScheduler

  verify_low   replied in  13.2s  -> 'LOW'
  verify_high  replied in   8.5s  -> 'HIGH'
  served first: verify_high

  ---- result: WORKS ----
  HIGH was served first even though LOW was submitted first, so priority is
  deciding the order
```

Exit status is 0 when the observed behaviour matches the policy. Under `fifo`
the two requests are usually merged into one model call and finish together --
reported as such, because that is correct for a batching policy and is exactly
why `fifo` cannot make a latency difference between priorities.

## set_policy.py

Show or change the kernel's scheduling policy **while it is running**, so a
demo does not have to pay the ~90 second restart.

```bash
python scripts/set_policy.py                       # what is running now
python scripts/set_policy.py priority              # switch to it
python scripts/set_policy.py fifo
python scripts/set_policy.py round_robin --time-slice 0.5
python scripts/set_policy.py priority --aging-interval 3
```

Requests that were accepted but not yet dispatched are carried over to the new
policy rather than dropped, so a switch never strands an agent. The switch
waits for the model call in flight to finish first, because a running
generation cannot be interrupted -- so it can take as long as one model
response. An unknown policy name is rejected and the running scheduler is left
alone.

Equivalently, over HTTP:

```bash
curl http://localhost:8000/core/scheduler
curl -X POST http://localhost:8000/core/scheduler/policy \
     -H "Content-Type: application/json" \
     -d '{"policy": "priority", "options": {"aging_interval": 3}}'
```

## run_terminal.py

The AIOS terminal. Each terminal window is one agent tab: it chats with the
kernel, and every message becomes an LLM syscall that the scheduling policy has
to order. Two options make a tab's place in that order visible:

- `--model` picks the backend the tab submits to -- `ollama`, `gemini` or
  `groq`, or any `<backend>:<model name>` configured in `config.yaml`;
- `--priority` sets the level its requests carry. Left out, the level follows
  the model: **ollama → high, gemini → normal (medium), groq → low**.

`--name` gives the tab its own agent identity, so the kernel log says *which*
tab is waiting instead of showing four identical `terminal` agents.

On PowerShell, one command opens all four tabs (the kernel must be running):

```powershell
.\scripts\run_tabs.ps1            # open the four tabs, one window each
.\scripts\run_tabs.ps1 -DryRun    # print the commands instead
```

or start them by hand:

```bash
# terminal 1: the kernel
scripts/run_kernel.sh

# terminals 2-5: one tab each, a different model and priority per tab
.venv/Scripts/python.exe scripts/run_terminal.py --name ollama_tab --model ollama --mode chat   # high
.venv/Scripts/python.exe scripts/run_terminal.py --name gemini_tab --model gemini --mode chat   # normal
.venv/Scripts/python.exe scripts/run_terminal.py --name groq_tab   --model groq   --mode chat   # low
.venv/Scripts/python.exe scripts/run_terminal.py --name urgent_tab --model gemini --priority high
```

Then type a message in each tab. With `scheduler.policy: priority` the kernel
terminal prints the queue it is choosing from, so a `high` message typed in one
tab is served before an older `low` one still waiting in another:

```
QUEUED   22:09:38  groq_tab (low)  queue=1
QUEUED   22:09:38  ollama_tab (high)  queue=2
RUN      22:09:38  ollama_tab (high)  waited 0.1s / 0 rounds  effective=high
DONE     22:09:39  ollama_tab  took 1.1s  thread=3
READY    22:09:39  next -> groq_tab(low,waited 1)
```

Change a tab's settings without restarting it:

| Command | Effect |
|---|---|
| `/priority <high\|normal\|low\|auto>` | this tab's level (`auto` follows the model again) |
| `/model <ollama\|gemini\|groq\|<name>>` | which backend the kernel routes to |
| `/name <agent>` | this tab's identity in the kernel log |
| `/scheduler` | the kernel's active policy, and this tab's priority in it |
| `/models` | the tab table, plus the models the kernel has loaded |
| `/status` | whether the kernel is up |
| `/chat`, `/file`, `/auto`, `/help`, `/exit` | the original terminal modes |

`--mode chat` skips intent routing, so each message is exactly one LLM syscall
-- fewer moving parts when watching the scheduler. The default mode is `auto`.

Two things worth knowing:

- **The same tabs work under every policy.** `fifo` and `round_robin` accept the
  `priority` field and ignore it, so under those policies the tabs behave
  exactly as they did before. Switch with `scripts/set_policy.py` and compare
  the kernel log rather than expecting an error.
- **Priority orders *queued* requests.** A message only waits behind another if
  the model is already busy, so the ordering is easiest to see by typing into
  all the tabs close together. The local Ollama model is the slowest one, which
  makes it the easiest to pile requests up behind.

## agent_tab.py

One interactive agent "tab" that talks to a running kernel. Open one terminal
per agent, give each a different `--priority`, and the kernel terminal prints
the scheduling decisions live.

```bash
# terminal 1: the kernel
scripts/run_kernel.sh

# terminals 2-3: the tabs
python scripts/agent_tab.py --agent chat_agent   --priority high
python scripts/agent_tab.py --agent report_agent --priority low
```

Interactive commands: `/priority <high|normal|low>` to change this tab's
priority, `/agent <name>`, `/status`, `/help`, `/exit`.

`--send "message"` submits a single message and exits, which is useful for
scripting a workload:

```bash
python scripts/agent_tab.py --agent chat_agent --priority high --send "hello"
```

The client uses only the standard library, so it starts instantly and needs
neither the kernel's dependencies nor a model backend.

`run_terminal.py` above is the same idea with the real AIOS terminal UI and a
per-tab model; this script is the dependency-free version. Both submit to the
same `POST /query` endpoint with a `priority` field.

## demo_priority_scheduling.py

Compare scheduling policies on the same workload and print a Gantt chart per
policy, plus per-agent response and waiting times. No model backend is needed:
a simulated clock stands in for `LLMAdapter`, so runs are deterministic.

```bash
python scripts/demo_priority_scheduling.py                  # fifo vs priority
python scripts/demo_priority_scheduling.py --policy priority
python scripts/demo_priority_scheduling.py --scenario starvation
python scripts/demo_priority_scheduling.py --config aios/config/config.yaml
```

The policy is chosen by `scheduler.policy` in `config.yaml`; `fcfs`,
`round_robin` and `priority` are selectable, and the starvation scenario prints
the low-priority request's wait in dispatch rounds next to the aging bound.

Note that `demo_priority_scheduling.py` measures the *policy* against a
simulated clock, while `agent_tab.py` drives the real kernel end to end. The
first is the reproducible experiment; the second is what you watch.
