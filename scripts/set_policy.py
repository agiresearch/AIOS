"""Show or change the AIOS kernel's scheduling policy while it is running.

The policy is read from ``config.yaml`` when the kernel starts, but the kernel
also accepts a change at runtime, so a demo can switch policy without paying
the ~90 second restart.

```bash
python scripts/set_policy.py                       # show the policy in effect
python scripts/set_policy.py priority              # switch to it
python scripts/set_policy.py fifo
python scripts/set_policy.py priority --aging-interval 3
python scripts/set_policy.py round_robin --time-slice 0.5
```

Requests that were accepted but not yet dispatched are carried over to the new
policy rather than dropped, so switching never strands an agent. The switch
waits for the model call in flight to finish, because a running generation
cannot be interrupted -- so it can take as long as one model response.

Uses only the standard library, so it needs neither the kernel's dependencies
nor a model backend.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

DEFAULT_SERVER = "http://localhost:8000"

#: A switch waits for the in-flight model call, so allow for a slow one.
DEFAULT_TIMEOUT = 900.0

PRIORITIES = ("high", "normal", "low")


def _call(
    url: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """Send a request to the kernel and return the decoded JSON body."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        try:
            detail = json.loads(detail).get("detail", detail)
        except (ValueError, AttributeError):
            pass
        raise SystemExit(f"  kernel rejected the request (HTTP {error.code}): {detail}")
    except Exception as error:
        raise SystemExit(
            f"  could not reach the kernel at {url} ({error}).\n"
            f"  Is it running?  Start it with: scripts/run_kernel.sh"
        )


def _show(server: str) -> Dict[str, Any]:
    """Print the policy the kernel is running and return the raw response."""
    info = _call(f"{server.rstrip('/')}/core/scheduler")
    dispatched = info.get("dispatched_llm_requests")
    print(f"  policy     : {info.get('policy')}")
    print(f"  scheduler  : {info.get('policy_class')}")
    print(f"  options    : {json.dumps(info.get('options') or {})}")
    print(
        f"  dispatched : {dispatched} LLM request(s)"
        if dispatched is not None
        else "  dispatched : (not reported by this policy)"
    )
    print(f"  available  : {', '.join(info.get('available_policies') or [])}")
    return info


def build_options(args: argparse.Namespace) -> Dict[str, Any]:
    """Collect the options the caller supplied, leaving the rest unset.

    Keys the selected policy does not declare are ignored by the kernel, so it
    is safe to pass an option that belongs to a different policy.
    """
    supplied = {
        "aging_interval": args.aging_interval,
        "default_priority": args.default_priority,
        "batch_interval": args.batch_interval,
        "time_slice": args.time_slice,
    }
    return {key: value for key, value in supplied.items() if value is not None}


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(
        prog="set_policy.py",
        description=(
            "Show or change the AIOS kernel's scheduling policy while it runs."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  set_policy.py                        # what is running now\n"
            "  set_policy.py priority\n"
            "  set_policy.py fifo\n"
            "  set_policy.py priority --aging-interval 3\n"
            "  set_policy.py round_robin --time-slice 0.5\n"
        ),
    )
    parser.add_argument(
        "policy",
        nargs="?",
        help="policy to switch to: fifo (alias fcfs), round_robin (alias rr), "
        "priority. Omit to just show the current one.",
    )
    parser.add_argument(
        "--aging-interval",
        type=int,
        help="priority policy: dispatch rounds a request waits to gain a level",
    )
    parser.add_argument(
        "--default-priority",
        choices=PRIORITIES,
        help="priority policy: level assumed when a request carries none",
    )
    parser.add_argument(
        "--batch-interval",
        type=float,
        help="fifo policy: seconds of requests collected into one batch",
    )
    parser.add_argument(
        "--time-slice",
        type=float,
        help="round_robin policy: seconds each request gets before moving on",
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER,
        help="kernel base URL (default: %(default)s)",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Show the current policy, or switch to another one."""
    args = build_parser().parse_args(argv)
    server = args.server.rstrip("/")

    if args.policy is None:
        _show(server)
        return 0

    payload: Dict[str, Any] = {"policy": args.policy}
    options = build_options(args)
    if options:
        payload["options"] = options

    print(f"  switching to '{args.policy}'...")
    print("  (waiting for any model call in flight to finish)")
    result = _call(f"{server}/core/scheduler/policy", payload)

    print(
        f"  {result.get('previous')} -> {result.get('policy')}"
        f"  [{result.get('policy_class')}]"
    )
    if result.get("released_requests"):
        print(
            f"  {result['released_requests']} accepted-but-undispatched "
            f"request(s) carried over to the new scheduler"
        )
    if result.get("options"):
        print(f"  options: {json.dumps(result['options'])}")
    print()
    _show(server)
    return 0


if __name__ == "__main__":
    sys.exit(main())
