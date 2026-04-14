from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
import os
import sys

# Ensure the project root is on the path so aios
# can be imported when running from scripts/
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

from list_agents import get_offline_agents, get_online_agents

from cerebrum.llm.apis import llm_chat, llm_operate_file

from cerebrum.storage.apis import mount

from aios.terminal.intent_router import (
    IntentRouter,
    Intent,
    build_llm_classify_fn,
)

class AIOSTerminal:
    def __init__(self):
        self.console = Console()
        
        self.style = Style.from_dict({
            'prompt': '#00ff00 bold',  
            'path': '#0000ff bold',    
            'arrow': '#ff0000',       
        })
        
        self.session = PromptSession(style=self.style)
        
        self.current_dir = os.getcwd()
        
        self.mode = "auto"
        self.conversation_history = []
        llm_fn = build_llm_classify_fn("terminal")
        self.router = IntentRouter(llm_classify_fn=llm_fn)
        
        # self.storage_client = StorageClient()

    def get_prompt(self, extra_str=None):
        username = os.getenv('USER', 'user')
        path = os.path.basename(self.current_dir)
        mode_indicator = f'[{self.mode}] '
        if extra_str:
            return [
                ('class:prompt', mode_indicator),
                ('class:prompt', f'🚀 {username}'),
                ('class:arrow', ' ⟹  '),
                ('class:path', f'{path}'),
                ('class:arrow', ' ≫ '),
                ('class:prompt', extra_str)
            ]
        else:
            return [
                ('class:prompt', mode_indicator),
                ('class:prompt', f'🚀 {username}'),
                ('class:arrow', ' ⟹  '),
                ('class:path', f'{path}'),
                ('class:arrow', ' ≫ ')
            ]

    def display_help(self):
        help_table = Table(show_header=True, header_style="bold magenta")
        help_table.add_column("Command", style="cyan")
        help_table.add_column("Description", style="green")
        
        # Add command descriptions
        help_table.add_row("help", "Show this help message")
        help_table.add_row("exit", "Exit the terminal")
        help_table.add_row("/chat", "Switch to chat mode (all input → chat)")
        help_table.add_row("/file", "Switch to file mode (all input → file ops)")
        help_table.add_row("/auto", "Switch to auto mode (intent routing)")
        # help_table.add_row("list agents --offline", "List all available offline agents")
        help_table.add_row("list agents --online", "List all available agents on the agenthub")
        help_table.add_row("<natural language>", "Routed automatically based on current mode")
        
        self.console.print(Panel(help_table, title="Available Commands", border_style="blue"))
        self.console.print(f"\nCurrent mode: [bold]{self.mode}[/bold]")

    def handle_slash_command(self, command):
        """Returns True if command was a slash command."""
        cmd = command.strip().lower()
        if cmd == "/chat":
            self.mode = "chat"
            self.console.print("[cyan]Switched to chat mode[/cyan]")
            return True
        if cmd == "/file":
            self.mode = "file"
            self.console.print("[cyan]Switched to file mode[/cyan]")
            return True
        if cmd == "/auto":
            self.mode = "auto"
            self.console.print("[cyan]Switched to auto mode[/cyan]")
            return True
        return False

    def route_input(self, user_input):
        """Dispatch user input based on current mode."""
        if self.mode == "chat":
            return self._send_chat(user_input)
        if self.mode == "file":
            return self._send_file(user_input)
        # auto mode
        result = self.router.classify(user_input)
        self.console.print(
            f"[dim][{result.intent.value}][/dim]"
        )
        if result.intent == Intent.CHAT:
            return self._send_chat(user_input)
        return self._send_file(user_input)

    def _send_chat(self, user_input):
        """Send input through the chat/personalization pipeline."""
        self.conversation_history.append(
            {"role": "user", "content": user_input}
        )
        response = llm_chat(
            agent_name="terminal",
            messages=list(self.conversation_history),
        )
        resp = response.get("response", "")
        if isinstance(resp, dict):
            assistant_msg = resp.get(
                "response_message", str(resp)
            )
        elif hasattr(resp, "response_message"):
            assistant_msg = resp.response_message
        else:
            assistant_msg = str(resp)
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_msg}
        )
        return assistant_msg

    def _send_file(self, user_input):
        """Send input through the file operation pipeline."""
        return llm_operate_file(
            agent_name="terminal",
            messages=[
                {"role": "user", "content": user_input}
            ],
        )

    def handle_list_agents(self, args: str):
        """Handle the 'list agents' command with different parameters.
        
        Args:
            args: The arguments passed to the list agents command (--offline or --online)
        """
        if '--offline' in args:
            agents = get_offline_agents()
            self.console.print("\nAgents that have been installed:")
            for agent in agents:
                self.console.print(f"- {agent}")
        elif '--online' in args:
            agents = get_online_agents()
            self.console.print("\nAvailable agents on the agenthub:")
            for agent in agents:
                self.console.print(f"- {agent}")
        else:
            self.console.print("[red]Invalid parameter. Use --offline or --online[/red]")
            self.console.print("Example: list agents --offline")

    def run(self):
        welcome_msg = Text("Welcome to AIOS Terminal! Type 'help' for available commands.", style="bold cyan")
        self.console.print(Panel(welcome_msg, border_style="green"))
        
        root_dir = self.current_dir + "/root"
        
        while True:
            mount_choice = self.session.prompt(self.get_prompt(extra_str=f"Do you want to mount AIOS Semantic File System to a specific directory you want? By default, it will be mounted at {root_dir}. [y/n] "))
            if mount_choice == 'y':
                root_dir = self.session.prompt(self.get_prompt(extra_str=f"Enter the absolute path of the directory to mount: "))
                break
            elif mount_choice == 'n':
                # self.console.print("[red]Storage not mounted. Some features may be unavailable.[/red]")
                break
            else:
                self.console.print("[red]Invalid input. Please enter 'y' or 'n'.[/red]")
                
        # breakpoint()
        mount(agent_name="terminal", root_dir=root_dir)
        
        mounted_message = Text(f"The semantic file system is mounted at {root_dir}", style="bold cyan")

        self.console.print(mounted_message)
                
        while True:
            try:
                command = self.session.prompt(self.get_prompt())
                
                if command == 'exit':
                    self.console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                    
                if command == 'help':
                    self.display_help()
                    continue
                
                if command.startswith('list agents'):
                    args = command[len('list agents'):].strip()
                    self.handle_list_agents(args)
                    continue
                
                if self.handle_slash_command(command):
                    continue
                
                command_response = self.route_input(command)
                command_output = Text(command_response, style="bold green")
                self.console.print(command_output)
                
                # response = self._post_semantic_command(command)
                
                # if cmd in self.commands:
                #     self.commands[cmd](*args)
                # else:
                #     self.console.print(f"[red]Unknown command: {cmd}[/red]")
                    
            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                self.console.print(f"[red]Error: {str(e)}[/red]")

if __name__ == "__main__":
    terminal = AIOSTerminal()
    terminal.run()