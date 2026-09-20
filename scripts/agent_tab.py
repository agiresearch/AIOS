"""One interactive "tab" that talks to a running AIOS kernel.

Open several terminals, run this script in each with a different ``--agent`` and
``--priority``, and the kernel terminal prints the scheduling decisions live::

    # terminal 1 (the kernel)
    scripts/run_kernel.sh

    # terminals 2..5 (the tabs)
    .venv/Scripts/python.exe scripts/agent_tab.py --agent chat_agent   --priority high
    .venv/Scripts/python.exe scripts/agent_tab.py --agent report_agent --priority low

Each tab is an independent agent identity submitting LLM requests to the
kernel's ``POST /query`` endpoint. With ``scheduler.policy: priority`` the
kernel orders the *queued* requests by priority, so a ``high`` message typed in
one tab is served before an older ``low`` one still waiting in another, and the
kernel log shows the queue it is choosing from.

The client deliberately uses only the standard library: it starts instantly and
does not need the kernel's dependencies, the model backends, or a GPU. All it
needs is a reachable kernel.

Usage:
    agent_tab.py --agent chat_agent --priority high
    agent_tab.py --agent batch_agent --priority low --send "summarise the log"
    agent_tab.py --list-priorities

Interactive commands:
    /priority <high|normal|low>   change this tab's priority for later messages
    /agent <name>                 change this tab's agent identity
    /status                       ask the kernel whether it is healthy
    /help                         list the commands
    /exit                         quit (Ctrl-D also works)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

#: Priorities the kernel's priority policy understands, most urgent first.
PRIORITIES: Tuple[str, ...] = ("high", "normal", "low")

#: A model call can take minutes on a local backend, so the read timeout is
#: generous. It is a safety net against a hung kernel, not a scheduling signal.
DEFAULT_TIMEOUT = 900.0


class KernelUnreachable(Exception):
    """Raised when the kernel's HTTP endpoint cannot be reached."""


# ----------------------------------------------------------------------
# Kernel transport
# ----------------------------------------------------------------------
def query_kernel(
    server: str,
    agent: str,
    message: str,
    priority: Optional[str],
    history: List[Dict[str, str]],
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[str, float]:
    """Send one chat message to the kernel and return ``(reply, seconds)``.

    The reply is the assistant message; ``seconds`` is how long the caller was
    blocked, which is the wait a user actually experiences. Priority is passed
    as a top-level field of the request so the kernel can order it against
    other agents' queued requests.

    Raises:
        KernelUnreachable: If the kernel does not answer.
    """
    payload: Dict[str, Any] = {
        "agent_name": agent,
        "query_type": "llm",
        "query_data": {
            "messages": history + [{"role": "user", "content": message}],
            "action_type": "chat",
        },
    }
    if priority is not None:
        payload["priority"] = priority

    request = urllib.request.Request(
        f"{server.rstrip('/')}/query",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise KernelUnreachable(f"kernel returned HTTP {error.code}: {detail}")
    except Exception as error:  # URLError, timeout, connection refused, ...
        raise KernelUnreachable(
            f"could not reach the kernel at {server} ({error}).\n"
            f"Is it running?  Start it with: scripts/run_kernel.sh"
        )

    return _extract_reply(body), time.time() - started


def kernel_status(server: str, timeout: float = 10.0) -> str:
    """Return the kernel's human-readable status, or a failure description."""
    try:
        with urllib.request.urlopen(
            f"{server.rstrip('/')}/status", timeout=timeout
        ) as response:
            body = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return f"unreachable ({error})"
    return str(body.get("message", body))


def _extract_reply(body: Dict[str, Any]) -> str:
    """Pull the assistant text out of a kernel ``/query`` response.

    The kernel returns the executor's result dict, whose ``response`` field is a
    Cerebrum ``LLMResponse``. Depending on how it was serialised it arrives as a
    dict or as an object, so both shapes are handled.
    """
    result = body.get("response", body)

    if isinstance(result, dict):
        message = result.get("response_message")
        error = result.get("error")
        if message is None and error:
            return f"<kernel error: {error}>"
        return str(message) if message is not None else json.dumps(result)

    if hasattr(result, "response_message"):
        return str(result.response_message)

    return str(result)


# ----------------------------------------------------------------------
# Terminal presentation
# ----------------------------------------------------------------------
def _banner(agent: str, priority: str, server: str, width: int = 66) -> str:
    """Return the header printed once when a tab starts."""
    lines = [
        f"  AIOS agent tab",
        f"  agent     : {agent}",
        f"  priority  : {priority}",
        f"  server    : {server}",
    ]
    rule = "=" * width
    padded = "\n".join(line.ljust(width) for line in lines)
    return (
        f"{rule}\n{padded}\n{rule}\n"
        f"  Type a message and press Enter. The kernel terminal shows when\n"
        f"  this request is picked up and how long it waited.\n"
        f"  Commands: /priority, /agent, /status, /help, /exit\n"
    )


def _clock() -> str:
    """Return the current local time as ``HH:MM:SS``."""
    return time.strftime("%H:%M:%S")


def _print_reply(reply: str, seconds: float, indent: str = "  ") -> None:
    """Print an assistant reply with its turnaround time."""
    print(f"[{_clock()}] reply after {seconds:.1f}s:")
    for line in reply.splitlines() or [""]:
        print(f"{indent}{line}")
    print()


def _handle_command(
    command: str,
    agent: str,
    priority: str,
    server: str,
) -> Tuple[bool, str, str]:
    """Handle a ``/command``.

    Returns:
        ``(handled, agent, priority)`` -- ``handled`` is ``False`` when the
        input was not a command, in which case the caller sends it as a message.
    """
    parts = command.split(maxsplit=1)
    name = parts[0].lower()
    argument = parts[1].strip() if len(parts) > 1 else ""

    if name in ("/exit", "/quit", "/q"):
        raise EOFError

    if name == "/help":
        print(
            "  /priority <high|normal|low>  change this tab's priority\n"
            "  /agent <name>                change this tab's agent identity\n"
            "  /status                      ask the kernel whether it is healthy\n"
            "  /exit                        quit\n"
        )
        return True, agent, priority

    if name == "/status":
        print(f"  kernel: {kernel_status(server)}\n")
        return True, agent, priority

    if name == "/priority":
        if argument.lower() not in PRIORITIES:
            print(f"  usage: /priority {'|'.join(PRIORITIES)}\n")
            return True, agent, priority
        print(f"  priority is now '{argument.lower()}'\n")
        return True, agent, argument.lower()

    if name == "/agent":
        if not argument:
            print("  usage: /agent <name>\n")
            return True, agent, priority
        print(f"  agent is now '{argument}'\n")
        return True, argument, priority

    print(f"  unknown command '{name}' -- try /help\n")
    return True, agent, priority


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def send_once(
    server: str,
    agent: str,
    priority: str,
    message: str,
) -> int:
    """Send a single message and print the reply. Returns a process exit code."""
    print(f"[{_clock()}] {agent} ({priority}) sent: {message}")
    try:
        reply, seconds = query_kernel(
            server, agent, message, priority, history=[]
        )
    except KernelUnreachable as error:
        print(f"  {error}", file=sys.stderr)
        return 1
    _print_reply(reply, seconds)
    return 0


def run_tab(server: str, agent: str, priority: str) -> int:
    """Run the interactive loop for one tab. Returns a process exit code."""
    print(_banner(agent, priority, server))
    history: List[Dict[str, str]] = []

    while True:
        try:
            line = input(f"{agent}[{priority}]> ")
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            return 0

        line = line.strip()
        if not line:
            continue

        if line.startswith("/"):
            try:
                _, agent, priority = _handle_command(
                    line, agent, priority, server
                )
            except EOFError:
                print("bye")
                return 0
            continue

        print(f"[{_clock()}] sent ({priority}) -- waiting for the kernel...")
        try:
            reply, seconds = query_kernel(
                server, agent, line, priority, history
            )
        except KernelUnreachable as error:
            print(f"  {error}\n")
            continue

        # Only successful exchanges are kept in the conversation, so a failed
        # request does not leave a dangling user turn in the history.
        history.append({"role": "user", "content": line})
        history.append({"role": "assistant", "content": reply})
        _print_reply(reply, seconds)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(
        prog="agent_tab.py",
        description=(
            "One interactive agent tab for a running AIOS kernel. Open one "
            "terminal per agent and run this in each."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  agent_tab.py --agent chat_agent --priority high\n"
            "  agent_tab.py --agent batch_agent --priority low\n"
            "  agent_tab.py --agent chat_agent --send 'hello'\n"
        ),
    )
    parser.add_argument(
        "--agent",
        default="agent",
        help="agent identity reported to the kernel (default: %(default)s)",
    )
    parser.add_argument(
        "--priority",
        default=os.getenv("AIOS_AGENT_PRIORITY", "normal"),
        choices=PRIORITIES,
        help="scheduling priority for messages from this tab (default: normal)",
    )
    parser.add_argument(
        "--server",
        default=os.getenv("AIOS_SERVER", "http://localhost:8000"),
        help="kernel base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--send",
        metavar="MESSAGE",
        help="send one message, print the reply and exit (no prompt)",
    )
    parser.add_argument(
        "--list-priorities",
        action="store_true",
        help="print the accepted priorities and exit",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Parse arguments and run one tab."""
    args = build_parser().parse_args(argv)

    if args.list_priorities:
        print("  " + ", ".join(PRIORITIES))
        return 0

    server = args.server.rstrip("/")

    if args.send:
        return send_once(server, args.agent, args.priority, args.send)

    if kernel_status(server).startswith("unreachable"):
        print(
            f"  warning: the kernel at {server} is not answering yet.\n"
            f"  Start it with scripts/run_kernel.sh, then send a message.\n",
            file=sys.stderr,
        )

    return run_tab(server, args.agent, args.priority)


if __name__ == "__main__":
    sys.exit(main())
