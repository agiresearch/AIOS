from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
import os
import shutil
from datetime import datetime
import sys
import requests
import json
from typing_extensions import Literal
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from enum import Enum

from cerebrum.client import Cerebrum

from cerebrum.llm.layer import LLMLayer
from cerebrum.overrides.layer import OverridesLayer
from cerebrum.storage.layer import StorageLayer
from cerebrum.memory.layer import MemoryLayer
from cerebrum.tool.layer import ToolLayer

from cerebrum.llm.communication import LLMQuery
from cerebrum.config.config_manager import config

from cerebrum.storage.communication import StorageQuery

# class QueryRequest(BaseModel):
#     agent_name: str
#     query_type: Literal["llm", "tool", "storage", "memory"]
#     query_data: LLMQuery | StorageQuery

# class StorageClient:
#     def __init__(self, base_url: str = "http://localhost:8000"):
#         self.base_url = base_url
#         self.client = self.setup_client()
#         self.client.connect()
        
def setup_client(
    llm_name: str = "gemini-1.5-flash",
    llm_backend: str = "google",
    root_dir: str = None,
    max_workers: int = None,
    memory_limit: int = None,
    aios_kernel_url: str = None
):
    # Use config values or override with provided parameters
    base_url = aios_kernel_url or config.get('kernel', 'base_url')
    root_dir = root_dir or config.get('client', 'root_dir')
    max_workers = max_workers or config.get('client', 'max_workers')
    
    client = Cerebrum(base_url=base_url)
    config.global_client = client

    try:
        client.add_llm_layer(LLMLayer(llm_name=llm_name, llm_backend=llm_backend)) \
            .add_storage_layer(StorageLayer(root_dir=root_dir)) \
            .add_memory_layer(MemoryLayer(memory_limit=512)) \
            .add_tool_layer(ToolLayer()) \
            .override_scheduler(OverridesLayer(max_workers=1))
        
        status = client.get_status()
        
        
        return client
    
    except Exception as e:
        # print(f"❌ Failed to initialize client: {str(e)}")
        raise
        

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
        
        # self.storage_client = StorageClient()

    def get_prompt(self, extra_str = None):
        username = os.getenv('USER', 'user')
        path = os.path.basename(self.current_dir)
        if extra_str:
            return [
                ('class:prompt', f'🚀 {username}'),
                ('class:arrow', ' ⟹  '),
                ('class:path', f'{path}'),
                ('class:arrow', ' ≫ '),
                ('class:prompt', extra_str)
            ]
        else:
            return [
                ('class:prompt', f'🚀 {username}'),
                ('class:arrow', ' ⟹  '),
                ('class:path', f'{path}'),
                ('class:arrow', ' ≫ ')
            ]
        
    def _post_mount(self, root_dir):
        query_data = StorageQuery(
            messages=[
                {"name": "mount", "parameters": {"root": root_dir}}
            ],
            operation_type="mount"
        )
        
        return self.storage_client._post(
            "/query",
            {
                "agent_name": "terminal",
                "query_type": "storage",
                "query_data": query_data.model_dump()
            }
        )
        
    def _post_semantic_command(self, query: str):
        query = LLMQuery(
            messages=[
                {"role": "user", "content": query}
            ],
            action_type="operate_file"
        )
        return self.storage_client._query_llm(agent_name="terminal", query=query)

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
                
        self.storage_client = setup_client(root_dir=root_dir)
        
        # breakpoint()
        self._post_mount(root_dir)
        
        mounted_message = Text(f"The semantic file system is mounted at {root_dir}", style="bold cyan")

        self.console.print(mounted_message)
                
        while True:
            try:
                command = self.session.prompt(self.get_prompt())
                
                if command == 'exit':
                    self.console.print("[yellow]Goodbye! 👋[/yellow]")
                    break
                
                command_response = self._post_semantic_command(command)
                
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