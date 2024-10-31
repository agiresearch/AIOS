import heapq
from threading import Lock, Event
from pympler import asizeof
from .interact import Interactor
from ..manager.manager import AgentManager
import os
import importlib
class AgentFactory:
    def __init__(self, agent_log_mode):
        self.agent_log_mode = agent_log_mode
        self.manager = AgentManager('https://my.aios.foundation/')

    def snake_to_camel(self, snake_str):
        components = snake_str.split('_')
        return ''.join(x.title() for x in components)

    def list_agents(self):
        agent_list = self.manager.list_available_agents()
        for agent in agent_list:
            print(agent)

    def load_agent_instance(self, compressed_name: str):
        # First try local loading
        try:
            author, name = compressed_name.split("/")
            module_name = ".".join(["pyopenagi", "agents", author, name, "agent"])
            class_name = self.snake_to_camel(name)
            agent_module = importlib.import_module(module_name)
            return getattr(agent_module, class_name)
        except (ImportError, AttributeError, ValueError):
            # If local loading fails, use original remote loading logic
            name_split = compressed_name.split('/')
            return self.manager.load_agent(*name_split)

    def activate_agent(self, agent_name: str, task_input):
        # First try local loading
        try:
            agent_class = self.load_agent_instance(agent_name)
        except:
            # If local loading fails, try downloading and loading
            try:
                agent_name = '/'.join(
                    self.manager.download_agent(
                        *agent_name.split('/')
                    ))
                agent_class = self.load_agent_instance(agent_name)
            except Exception as e:
                print(f"Warning: Both local and remote loading failed. Error: {str(e)}")
                raise

        agent = agent_class(
            agent_name=agent_name,
            task_input=task_input,
            log_mode=self.agent_log_mode
        )
        return agent

    def run_agent(self, agent_name, task_input):
        agent = self.activate_agent(
            agent_name=agent_name,
            task_input=task_input
        )
        output = agent.run()
        return output

    def print_agent(self):
        headers = ["Agent ID", "Agent Name", "Created Time", "Status", "Memory Usage"]
        data = []
        for id, agent in self.current_agents.items():
            agent_name = agent.agent_name
            created_time = agent.created_time
            status = agent.status
            memory_usage = f"{asizeof.asizeof(agent)} bytes"
            data.append(
                [id, agent_name, created_time, status, memory_usage]
            )
        self.print(headers=headers, data=data)

    def print(self, headers, data):
        column_widths = [
            max(len(str(row[i])) for row in [headers] + data) for i in range(len(headers))
        ]
        print("+" + "-" * (sum(column_widths) + len(headers) * 3 - 3) + "+")
        print(self.format_row(headers, column_widths))
        print("=" * (sum(column_widths) + len(headers) * 3 - 1))
        for i, row in enumerate(data):
            print(self.format_row(row, column_widths))
            if i < len(data):
                print("-" * (sum(column_widths) + len(headers) * 3 - 1))
        print("+" + "-" * (sum(column_widths) + len(headers) * 3 - 3) + "+")

    def format_row(self, row, widths, align="<"):
        row_str = " | ".join(f"{str(item):{align}{widths[i]}}" for i, item in enumerate(row))
        return row_str

    def deactivate_agent(self, aid):
        pass