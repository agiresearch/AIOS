"""Check that the kernel's scheduling policy is live and actually ordering work.

Two questions are worth distinguishing:

* **Which policy is running?** -- identity. Answered by ``GET /core/scheduler``.
* **Is it doing anything?** -- behaviour. Answered by submitting two requests
  with different priorities at the same instant and seeing which one is served
  first. If a policy were selected but the priority ignored, the identity check
  would still pass and this one would not.

The test:

1. send a LOW-priority request and a HIGH-priority request simultaneously, from
   two threads released by the same barrier, so both land in the same scheduling
   round;
2. record which reply arrives first;
3. compare that against what the running policy should do.

```bash
python scripts/verify_policy.py
python scripts/verify_policy.py --server http://localhost:8000
```

A run takes a few seconds plus one model response. Uses only the standard
library. Nothing is written to the kernel except the two requests, which are
ordinary chat messages.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_SERVER = "http://localhost:8000"

#: One model response, plus room for the loser to queue behind it.
DEFAULT_TIMEOUT = 300.0

#: Policies that serve requests in arrival order, so the first request should win.
ARRIVAL_ORDER_POLICIES = ("fifo", "round_robin")


def _post(
    url: str, payload: Dict[str, Any], timeout: float = DEFAULT_TIMEOUT
) -> Dict[str, Any]:
    """POST JSON to the kernel and return the decoded body."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get(url: str, timeout: float = 30.0) -> Dict[str, Any]:
    """GET JSON from the kernel and return the decoded body."""
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def read_policy(server: str) -> Dict[str, Any]:
    """Return the kernel's scheduler description."""
    return _get(f"{server.rstrip('/')}/core/scheduler")


def chat(
    server: str,
    agent: str,
    priority: str,
    message: str,
    barrier: threading.Barrier,
    results: Dict[str, Tuple[float, str]],
) -> None:
    """Submit one chat request, released together with its counterpart.

    Waiting on a barrier means both requests are put on the wire at the same
    instant, so they enter the same scheduling round rather than being separated
    by however long it took to start a thread.
    """
    payload = {
        "agent_name": agent,
        "query_type": "llm",
        "priority": priority,
        "query_data": {
            "messages": [{"role": "user", "content": message}],
            "action_type": "chat",
        },
    }
    try:
        barrier.wait(timeout=10)
    except threading.BrokenBarrierError:
        pass

    started = time.time()
    try:
        body = _post(f"{server.rstrip('/')}/query", payload)
        response = body.get("response")
        text = (
            response.get("response_message")
            if isinstance(response, dict)
            else str(response)
        )
    except Exception as error:  # noqa: BLE001 - reported as a failed run
        text = f"<request failed: {error}>"
    results[agent] = (time.time() - started, str(text))


def run_race(server: str) -> Tuple[str, Dict[str, Tuple[float, str]]]:
    """Send LOW then HIGH at the same instant; return which agent replied first."""
    barrier = threading.Barrier(2)
    results: Dict[str, Tuple[float, str]] = {}

    # ``low_agent`` is listed first so that under an arrival-order policy it is
    # the one the queue serves first.
    threads = [
        threading.Thread(
            target=chat,
            args=(
                server,
                "verify_low",
                "low",
                "Reply with exactly: LOW",
                barrier,
                results,
            ),
            daemon=True,
        ),
        threading.Thread(
            target=chat,
            args=(
                server,
                "verify_high",
                "high",
                "Reply with exactly: HIGH",
                barrier,
                results,
            ),
            daemon=True,
        ),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=DEFAULT_TIMEOUT + 60)

    if not results:
        return "<none>", results

    first = min(results, key=lambda agent: results[agent][0])
    return first, results


#: Two completions closer together than this are treated as simultaneous, which
#: is what a batching policy produces when it merges the pair into one call.
SAME_CALL_SECONDS = 0.25


def _verdict(
    policy: str,
    first: str,
    results: Dict[str, Tuple[float, str]],
) -> Tuple[bool, str]:
    """Say whether the observed behaviour matches what the policy should do.

    The interesting case is a tie: ``fifo`` collects requests for
    ``batch_interval`` seconds and sends them as one call, so the two requests
    finish together and there is no ordering to observe at all. That is correct
    behaviour for a batching policy -- and it is exactly why ``fifo`` cannot
    make a latency difference between priorities.
    """
    times = {agent: seconds for agent, (seconds, _) in results.items()}
    batched = (
        len(times) == 2
        and abs(times["verify_low"] - times["verify_high"]) < SAME_CALL_SECONDS
    )

    if policy == "priority":
        if batched:
            return (
                False,
                "both replies came back together, but the priority policy "
                "dispatches one request at a time -- re-run, the two requests "
                "probably did not land in the same scheduling round",
            )
        if first == "verify_high":
            return (
                True,
                "HIGH was served first even though LOW was submitted first, "
                "so priority is deciding the order",
            )
        return (
            False,
            "LOW was served before HIGH, which the priority policy should not "
            "do -- re-run before treating this as a failure, since the two "
            "requests may not have landed in the same scheduling round",
        )

    if policy in ARRIVAL_ORDER_POLICIES:
        if batched:
            return (
                True,
                f"'{policy}' merged both requests into a single model call, so "
                f"neither was served first and the priorities made no difference "
                f"-- expected, since '{policy}' has no notion of priority",
            )
        if first == "verify_low":
            return (
                True,
                f"'{policy}' served the earlier request first, ignoring the "
                f"priorities -- expected, since it has no notion of priority",
            )
        return (
            False,
            f"'{policy}' served HIGH first, but it has no notion of priority "
            f"-- re-run, since the two requests may not have landed in the "
            f"same scheduling round",
        )

    return False, f"'{policy}' is not a policy this check knows how to judge"


def main(argv: Optional[List[str]] = None) -> int:
    """Report the running policy and check that it is actually in effect."""
    parser = argparse.ArgumentParser(
        prog="verify_policy.py",
        description=(
            "Check the AIOS kernel's scheduling policy is live and ordering work."
        ),
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help="kernel base URL (default: %(default)s)",
    )
    args = parser.parse_args(argv)
    server = args.server.rstrip("/")

    try:
        info = read_policy(server)
    except Exception as error:  # noqa: BLE001
        print(f"  could not reach the kernel at {server} ({error})")
        print("  Start it with: scripts/run_kernel.sh")
        return 1

    policy = info.get("policy")
    print("  ---- identity ----")
    print(f"  policy     : {policy}")
    print(f"  scheduler  : {info.get('policy_class')}")
    print(f"  options    : {json.dumps(info.get('options') or {})}")
    print(f"  available  : {', '.join(info.get('available_policies') or [])}")

    print()
    print("  ---- behaviour ----")
    print("  sending LOW and HIGH at the same instant...")
    first, results = run_race(server)

    if not results:
        print("  no replies came back; is the model backend running?")
        return 1

    for agent in ("verify_low", "verify_high"):
        if agent in results:
            seconds, text = results[agent]
            print(f"  {agent:<12} replied in {seconds:5.1f}s  -> {text[:40]!r}")
    print(f"  served first: {first}")

    ok, message = _verdict(str(policy), first, results)
    print()
    print(f"  ---- result: {'WORKS' if ok else 'INCONCLUSIVE / WRONG'} ----")
    print(f"  {message}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
