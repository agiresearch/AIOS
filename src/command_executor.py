# This file parses commands given to simulator.py and evaluates them using agents


# Facilitates interaction with agents


# Enables commands to be executed concurrently
from concurrent.futures import ThreadPoolExecutor

class Executor:
    def __init__(self, agent_factory):
        self.agent_thread_pool = ThreadPoolExecutor(max_workers=64)
        self.command_table = {
            "run": self.run_agent,
            "print": self.print
        }
        self.agent_factory = agent_factory
        # self.agent_process_queue = agent_process_queue

    def execute(self, command):
        """Executes a given command."""
        command_type = command["command_type"]
        command_name = command["command_name"]
        command_body = command["command_body"]
        try:
            self.command_table[command_type](
                command_name,
                command_body
            )

        except KeyError:
            print("usage: command_type: [command_name] [command_body]")

    def print_agent_memory():
        pass

    def print(self, command_name = None, command_body = None):
        """List status of agent process."""
        if command_name == "agent":
            self.agent_factory.print_agent()
        elif command_name == "agent-process":
            return NotImplementedError

    def run_agent(self, agent_name, task_input):
        # self.agent_factory.activate_agent(agent_name, task_input)
        # print(agent_name, task_input)

        self.agent_thread_pool.submit(
            self.agent_factory.run_agent,
            agent_name,
            task_input
        )
        # result = task.result()
