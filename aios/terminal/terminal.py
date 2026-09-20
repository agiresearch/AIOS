"""The AIOS terminal: one interactive agent per terminal window.

The terminal is the front end of the kernel's syscall path -- every message it
sends becomes an LLM syscall, and the kernel's scheduling policy decides when
that syscall reaches the model. This terminal makes the tab's place in that
order explicit:

* ``--model`` selects the backend the tab submits to (``ollama``, ``gemini`` or
  ``groq``), which is what the kernel routes on;
* ``--priority`` sets the level the tab's requests carry, and defaults to the
  level of the tab's backend (``ollama`` high, ``gemini`` normal, ``groq`` low);
* ``--name`` gives the tab its own agent identity, so the kernel log says which
  tab is waiting instead of showing four identical ``terminal`` agents.

Both are changeable while the tab runs::

    /priority high|normal|low|auto
    /model ollama|gemini|groq|<name>|<backend>:<model>

Requests are sent with the tab's priority and model attached, so a high-priority
message typed in one tab is served before an older low-priority one still queued
in another. Under ``fifo`` and ``round_robin`` the priority is ignored by the
kernel and the tabs behave exactly as before, which is what makes the three
policies comparable side by side.

Usage:
    python scripts/run_terminal.py --name ollama_tab --model ollama --mode chat
    python scripts/run_terminal.py --name gemini_tab --model gemini --mode chat
    python scripts/run_terminal.py --name groq_tab   --model groq   --mode chat
    python scripts/run_terminal.py --list-models

``--mode chat`` bypasses intent routing, so each message is exactly one LLM
syscall -- fewer moving parts when watching the scheduler. The default mode is
``auto``, which routes between chat and file operations as before.
"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence

from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aios.terminal import tab_client
from aios.terminal.intent_router import (
    LLM_CLASSIFY_SYSTEM_PROMPT,
    Intent,
    IntentRouter,
)

#: Used when neither --server nor the Cerebrum configuration names a kernel.
DEFAULT_SERVER = "http://localhost:8000"

MODES = ("auto", "chat", "file")


def default_server() -> str:
    """Return the kernel URL, preferring the Cerebrum configuration."""
    try:
        from cerebrum.config.config_manager import config

        return config.get_kernel_url() or DEFAULT_SERVER
    except Exception:  # Cerebrum not importable: the CLI still works
        return DEFAULT_SERVER


def mount_agent_root(agent_name: str, root_dir: str) -> None:
    """Mount the semantic file system for this agent, if Cerebrum is available."""
    from cerebrum.storage.apis import mount

    mount(agent_name=agent_name, root_dir=root_dir)


class AIOSTerminal:
    """One interactive agent tab talking to a running AIOS kernel."""

    def __init__(
        self,
        agent_name: str = "terminal",
        priority: Optional[str] = None,
        model: Optional[Mapping[str, str]] = None,
        mode: str = "auto",
        server: str = DEFAULT_SERVER,
    ) -> None:
        """Create a tab.

        Args:
            agent_name: Identity the tab submits under.
            priority: Level for this tab's requests. When omitted, the level
                configured for the tab's backend is used.
            model: ``{"name", "backend"}`` the kernel should route to, or
                ``None`` to let the kernel pick.
            mode: ``auto`` (route each input), ``chat`` or ``file``.
            server: Base URL of the kernel.
        """
        self.console = Console()

        self.style = Style.from_dict(
            {
                "prompt": "#00ff00 bold",
                "path": "#0000ff bold",
                "arrow": "#ff0000",
            }
        )

        # Created on first use rather than here: prompt_toolkit needs a real
        # console, and building it eagerly would make the tab impossible to
        # construct -- and therefore to test -- outside an interactive shell.
        self._session: Optional[PromptSession] = None

        self.current_dir = os.getcwd()

        self.server = server.rstrip("/")
        self.agent_name = agent_name
        self.model: Optional[Dict[str, str]] = dict(model) if model else None
        self.mode = mode

        # A priority given on the command line is a choice the user made, so
        # switching model must not overwrite it. Otherwise the level follows the
        # tab's backend.
        self.priority_pinned = priority is not None
        self.priority: Optional[str] = (
            tab_client.normalise_priority(priority)
            if priority is not None
            else self._priority_for_model()
        )

        self.conversation_history: List[Dict[str, str]] = []
        self.router = IntentRouter(llm_classify_fn=self._build_classify_fn())

    @property
    def session(self) -> PromptSession:
        """Return the prompt session, creating it on first use."""
        if self._session is None:
            self._session = PromptSession(style=self.style)
        return self._session

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def _priority_for_model(self) -> Optional[str]:
        """Return the priority configured for the tab's current backend."""
        return tab_client.priority_for_backend(
            self.model["backend"] if self.model else None
        )

    def _set_model(self, spec: str) -> str:
        """Point the tab at another model, returning a message for the user.

        Raises:
            ValueError: If ``spec`` matches no known model.
        """
        self.model = tab_client.resolve_model(spec)
        if not self.priority_pinned:
            self.priority = self._priority_for_model()
        return (
            f"model: {self.model['name']} ({self.model['backend']})  "
            f"priority: {self.priority or 'kernel default'}"
        )

    def _set_priority(self, value: str) -> str:
        """Pin, or with ``auto`` unpin, the tab's priority."""
        if value.strip().lower() == "auto":
            self.priority_pinned = False
            self.priority = self._priority_for_model()
            return f"priority follows the model: {self.priority or 'kernel default'}"
        self.priority = tab_client.normalise_priority(value)
        self.priority_pinned = True
        return f"priority: {self.priority}"

    def _identity(self) -> str:
        """Return ``<priority>@<model>`` for the prompt line."""
        model = self.model["name"] if self.model else "kernel default"
        return f"{self.priority or 'default'}@{model}"

    def _build_classify_fn(self):
        """Build the intent classifier, routed through this tab's priority.

        Using the tab's own priority and model keeps ``auto`` mode coherent:
        the classification request is scheduled like the message it precedes.
        """

        def classify(user_input: str) -> Intent:
            payload = tab_client.build_llm_payload(
                self.agent_name,
                [
                    {"role": "system", "content": LLM_CLASSIFY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_input},
                ],
                priority=self.priority,
                model=self.model,
            )
            body = tab_client.post_query(self.server, payload)
            raw = tab_client.extract_reply(body).strip().lower()
            return Intent.FILE_OPERATION if "file" in raw else Intent.CHAT

        return classify

    # ------------------------------------------------------------------
    # Prompt and help
    # ------------------------------------------------------------------
    def get_prompt(self, extra_str: Optional[str] = None):
        prefix = [
            ("class:prompt", f"[{self.mode}] "),
            ("class:prompt", f"🚀 {self.agent_name}"),
            ("class:arrow", " ⟹  "),
            ("class:path", self._identity()),
        ]
        if extra_str:
            return prefix + [("class:arrow", " ≫ "), ("class:prompt", extra_str)]
        return prefix + [("class:arrow", " ≫ ")]

    def display_help(self):
        help_table = Table(show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="green")

        help_table.add_row("help", "Show this help message")
        help_table.add_row("exit", "Exit the terminal")
        help_table.add_row("/priority <high|normal|low|auto>", "Set this tab's scheduling priority")
        help_table.add_row("/model <ollama|gemini|groq|name>", "Set the model the kernel routes to")
        help_table.add_row("/name <agent>", "Change this tab's agent identity")
        help_table.add_row("/scheduler", "Show the kernel's active scheduling policy")
        help_table.add_row("/models", "Show the models the kernel has loaded")
        help_table.add_row("/status", "Ask the kernel whether it is healthy")
        help_table.add_row("/chat", "Switch to chat mode (all input → chat)")
        help_table.add_row("/file", "Switch to file mode (all input → file ops)")
        help_table.add_row("/auto", "Switch to auto mode (intent routing)")
        help_table.add_row("list agents --online", "List all available agents on the agenthub")
        help_table.add_row("<natural language>", "Routed automatically based on current mode")

        self.console.print(Panel(help_table, title="Available Commands", border_style="blue"))
        self.console.print(
            f"\nCurrent mode: [bold]{self.mode}[/bold]  "
            f"agent: [bold]{self.agent_name}[/bold]  "
            f"priority: [bold]{self.priority or 'kernel default'}[/bold]  "
            f"model: [bold]{self.model['name'] if self.model else 'kernel default'}[/bold]"
        )

    def _show_scheduler(self) -> None:
        """Print the kernel's active policy, and its alternatives."""
        try:
            info = tab_client.kernel_scheduler(self.server)
        except tab_client.KernelUnreachable as error:
            self.console.print(f"[red]{error}[/red]")
            return
        self.console.print(f"  policy     : [bold]{info.get('policy')}[/bold]")
        self.console.print(f"  scheduler  : {info.get('policy_class')}")
        self.console.print(f"  options    : {info.get('options') or {}}")
        self.console.print(
            f"  available  : {', '.join(info.get('available_policies') or [])}"
        )
        self.console.print(
            "\n  this tab submits at priority "
            f"[bold]{self.priority or 'kernel default'}[/bold]"
            + (
                " — only the 'priority' policy acts on it"
                if info.get("policy") != "priority"
                else ""
            )
        )

    def _show_models(self) -> None:
        """Print the tab table and what the kernel actually has loaded."""
        table = Table(title="Tabs (--model)", show_header=True, header_style="bold magenta")
        table.add_column("--model", style="cyan")
        table.add_column("model")
        table.add_column("backend", style="green")
        table.add_column("priority", style="yellow")
        for key, name, backend, priority in tab_client.tab_table():
            table.add_row(key, name, backend, priority)
        self.console.print(table)

        try:
            loaded = tab_client.kernel_models(self.server)
        except tab_client.KernelUnreachable as error:
            self.console.print(f"[red]{error}[/red]")
            return
        self.console.print("Kernel models:")
        for entry in loaded:
            self.console.print(
                f"  - {entry.get('name')} ({entry.get('backend')})"
            )

    # ------------------------------------------------------------------
    # Slash commands
    # ------------------------------------------------------------------
    def handle_slash_command(self, command: str) -> bool:
        """Handle a slash command, returning True when one was recognised."""
        stripped = command.strip()
        lowered = stripped.lower()

        if lowered == "/chat":
            self.mode = "chat"
            self.console.print("[cyan]Switched to chat mode[/cyan]")
            return True
        if lowered == "/file":
            self.mode = "file"
            self.console.print("[cyan]Switched to file mode[/cyan]")
            return True
        if lowered == "/auto":
            self.mode = "auto"
            self.console.print("[cyan]Switched to auto mode[/cyan]")
            return True

        if lowered.startswith("/priority"):
            value = stripped[len("/priority") :].strip()
            if not value:
                self.console.print(
                    f"priority: [bold]{self.priority or 'kernel default'}[/bold]"
                    f" ({'pinned' if self.priority_pinned else 'from the model'})"
                )
                return True
            try:
                message = self._set_priority(value)
            except ValueError as error:
                self.console.print(f"[red]{error}[/red]")
                return True
            self.console.print(f"[cyan]{message}[/cyan]")
            return True

        if lowered.startswith("/model"):
            value = stripped[len("/model") :].strip()
            if not value:
                self.console.print(f"model: {self._identity()}")
                return True
            try:
                message = self._set_model(value)
            except ValueError as error:
                self.console.print(f"[red]{error}[/red]")
                return True
            self.console.print(f"[cyan]{message}[/cyan]")
            return True

        if lowered.startswith("/name"):
            value = stripped[len("/name") :].strip()
            if value:
                self.agent_name = value
                self.console.print(f"[cyan]agent: {self.agent_name}[/cyan]")
            else:
                self.console.print(f"agent: {self.agent_name}")
            return True

        if lowered in ("/scheduler", "/policy"):
            self._show_scheduler()
            return True
        if lowered == "/models":
            self._show_models()
            return True
        if lowered == "/status":
            self.console.print(tab_client.kernel_status(self.server))
            return True
        if lowered == "/help":
            self.display_help()
            return True
        return False

    # ------------------------------------------------------------------
    # Sending work
    # ------------------------------------------------------------------
    def route_input(self, user_input: str):
        """Dispatch user input based on the current mode."""
        if self.mode == "chat":
            return self._send_chat(user_input)
        if self.mode == "file":
            return self._send_file(user_input)
        result = self.router.classify(user_input)
        self.console.print(f"[dim][{result.intent.value}][/dim]")
        if result.intent == Intent.CHAT:
            return self._send_chat(user_input)
        return self._send_file(user_input)

    def _post(self, messages: Sequence[Mapping[str, Any]], action_type: str, tools=None):
        """Send one LLM request carrying this tab's priority and model."""
        payload = tab_client.build_llm_payload(
            self.agent_name,
            messages,
            action_type=action_type,
            priority=self.priority,
            model=self.model,
            tools=tools,
        )
        return tab_client.extract_reply(
            tab_client.post_query(self.server, payload)
        )

    def _send_chat(self, user_input: str) -> str:
        """Send input through the chat pipeline and record the turn."""
        self.conversation_history.append({"role": "user", "content": user_input})
        try:
            assistant_msg = self._post(self.conversation_history, "chat")
        except tab_client.KernelUnreachable as error:
            self.conversation_history.pop()
            return str(error)
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_msg}
        )
        return assistant_msg

    def _send_file(self, user_input: str) -> str:
        """Send input through the file operation pipeline."""
        try:
            return self._post(
                [{"role": "user", "content": user_input}], "operate_file", tools=[]
            )
        except tab_client.KernelUnreachable as error:
            return str(error)

    # ------------------------------------------------------------------
    # Agents listing
    # ------------------------------------------------------------------
    def handle_list_agents(self, args: str):
        """Handle the 'list agents' command with different parameters."""
        try:
            from scripts.list_agents import get_offline_agents, get_online_agents
        except Exception as error:  # Cerebrum or its cache is unavailable
            self.console.print(f"[red]Cannot list agents: {error}[/red]")
            return

        if "--offline" in args:
            agents = get_offline_agents()
            self.console.print("\nAgents that have been installed:")
            for agent in agents:
                self.console.print(f"- {agent}")
        elif "--online" in args:
            agents = get_online_agents()
            self.console.print("\nAvailable agents on the agenthub:")
            for agent in agents:
                self.console.print(f"- {agent}")
        else:
            self.console.print("[red]Invalid parameter. Use --offline or --online[/red]")
            self.console.print("Example: list agents --offline")

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        welcome = Panel(
            Text(
                "Welcome to AIOS Terminal! Type 'help' for available commands.",
                style="bold cyan",
            ),
            border_style="green",
        )
        model_line = (
            f"{self.model['name']} ({self.model['backend']})"
            if self.model
            else "kernel default"
        )
        self.console.print(welcome)
        self.console.print(
            f"  agent    : [bold]{self.agent_name}[/bold]\n"
            f"  mode     : [bold]{self.mode}[/bold]\n"
            f"  priority : [bold]{self.priority or 'kernel default'}[/bold]"
            f"{'' if self.priority_pinned else ' (follows the model)'}\n"
            f"  model    : [bold]{model_line}[/bold]\n"
            f"  kernel   : {self.server}\n"
            f"  change it with /priority, /model, /name; /help for everything"
        )

        root_dir = self.current_dir + "/root"

        while True:
            mount_choice = self.session.prompt(
                self.get_prompt(
                    extra_str=(
                        "Do you want to mount AIOS Semantic File System to a "
                        f"specific directory you want? By default, it will be "
                        f"mounted at {root_dir}. [y/n] "
                    )
                )
            )
            if mount_choice == "y":
                root_dir = self.session.prompt(
                    self.get_prompt(
                        extra_str="Enter the absolute path of the directory to mount: "
                    )
                )
                break
            if mount_choice == "n":
                break
            self.console.print("[red]Invalid input. Please enter 'y' or 'n'.[/red]")

        try:
            mount_agent_root(self.agent_name, root_dir)
            self.console.print(
                Text(
                    f"The semantic file system is mounted at {root_dir}",
                    style="bold cyan",
                )
            )
        except Exception as error:
            # Chat still works against a kernel whose storage mount failed, so
            # report it and carry on rather than refusing to start.
            self.console.print(
                f"[yellow]File system not mounted ({error}); chat is unaffected[/yellow]"
            )

        while True:
            try:
                command = self.session.prompt(self.get_prompt())

                if command == "exit":
                    self.console.print("[yellow]Goodbye! 👋[/yellow]")
                    break

                if command == "help":
                    self.display_help()
                    continue

                if command.startswith("list agents"):
                    args = command[len("list agents") :].strip()
                    self.handle_list_agents(args)
                    continue

                if self.handle_slash_command(command):
                    continue

                command_response = self.route_input(command)
                self.console.print(Text(str(command_response), style="bold green"))

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as error:
                self.console.print(f"[red]Error: {str(error)}[/red]")


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(
        prog="run_terminal.py",
        description="Interactive AIOS agent tab that carries a scheduling priority.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  run_terminal.py --name ollama_tab --model ollama --mode chat\n"
            "  run_terminal.py --name gemini_tab --model gemini --mode chat\n"
            "  run_terminal.py --name groq_tab   --model groq   --mode chat\n"
            "  run_terminal.py --name urgent_tab --model gemini --priority high\n"
            "  run_terminal.py --list-models\n"
        ),
    )
    parser.add_argument(
        "--name",
        "-n",
        default="terminal",
        help="agent identity this tab submits under (default: %(default)s)",
    )
    parser.add_argument(
        "--priority",
        "-p",
        help="this tab's scheduling priority: high | normal (medium) | low. "
        "Default: the level of the chosen model's backend "
        f"({', '.join(f'{k}={v}' for k, v in tab_client.BACKEND_PRIORITIES.items())})",
    )
    parser.add_argument(
        "--model",
        "-m",
        help="model to submit to: "
        f"{', '.join(sorted(tab_client.TAB_MODELS))}, a model name, or "
        "'<backend>:<model name>'",
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default="auto",
        help="input routing: auto (classify), chat (one LLM syscall per message), "
        "file (default: %(default)s)",
    )
    parser.add_argument(
        "--server",
        default=default_server(),
        help="kernel base URL (default: %(default)s)",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="print the tab/model/priority table and exit",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Run one terminal tab."""
    args = build_parser().parse_args(argv)

    if args.list_models:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("--model", style="cyan")
        table.add_column("model")
        table.add_column("backend", style="green")
        table.add_column("priority", style="yellow")
        for key, name, backend, priority in tab_client.tab_table():
            table.add_row(key, name, backend, priority)
        Console().print(table)
        return 0

    try:
        priority = (
            tab_client.normalise_priority(args.priority)
            if args.priority is not None
            else None
        )
    except ValueError as error:
        build_parser().error(str(error))

    try:
        model = tab_client.resolve_model(args.model) if args.model else None
    except ValueError as error:
        build_parser().error(str(error))

    terminal = AIOSTerminal(
        agent_name=args.name,
        priority=priority,
        model=model,
        mode=args.mode,
        server=args.server,
    )
    terminal.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
