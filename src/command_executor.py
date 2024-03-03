import os

import subprocess

import sys

from agent_factory import (
    create_agent,
    destroy_agent
)

def print_agent_process():
    """List status of agent process."""
    pass

def exit_shell():
    """Exits the simulated shell."""
    print("Exiting shell.")
    exit()

def run_agent(agent_name):
    agent = create_agent(agent_name)

command_table = {
    "run": run_agent,
    "print": print_agent_process
}

def execute_command(command):
    """Executes a given command."""
    command_name = command[0]
    command_content = command[1]
    command_table[command[0]](command[1])
    