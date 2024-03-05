import os

import sys

from src.utils.global_param import (
    thread_pool,
    agent_process_queue,
    agent_table
)

import subprocess

class Executor:
    def __init__(self, agent_factory):
        # self.thread_pool = ThreadPoolExecutor(max_workers=MAX_WORKER_NUM)
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
    
        if command_type in self.command_table.keys():
            self.command_table[command_type](
                command_name,
                command_body
            )
    
        else:
            return NotImplementedError

    def print_agent_memory():
        pass

    def print(self, command_name = None, command_body = None):
        """List status of agent process."""
        if command_name == "agent":
            self.agent_factory.print()
        elif command_name == "agent-process":
            agent_process_queue.print()
            
    def exit_shell(self):
        """Exits the simulated shell."""
        print("Exiting shell.")
        exit()
    
    def run_agent(self, agent_name = None, task_input = None):
        agent_program = agent_table[agent_name]
        print(agent_program)
        args = ["--agent_name", agent_name, "--task_input", task_input]
        subprocess.run(["python3", "-m", agent_program] + args)
        
        # agent = self.agent_factory.activate_agent(agent_name, task_input)   
        # agent.run()
        # runner = thread_pool.submit(agent.run)

        # print(len(agent_process_queue))
        
        # deactivator = thread_pool.submit(self.agent_factory.deactivate_agent, agent)
