import os
import sys

from src.command_parser import (
    PunctuationParser,
    ChatGPTParser
)

from src.command_executor import (
    Executor
)

from src.llms import llms

from src.scheduler.fifo_scheduler import FIFOScheduler

import warnings

from src.agent_factory import (
    AgentFactory
)

from src.agents.agent_process import (
    AgentProcess,
    AgentProcessQueue
)

from src.utils.global_param import (
    thread_pool,
    agent_process_queue
)

import subprocess

def main():
    warnings.filterwarnings("ignore")
    # agent_process_queue.print()
    llm_type = "mistral-7b-instruct"
    llm = llms.LLMKernel(llm_type)

    parser = PunctuationParser(llm)

    agent_factory = AgentFactory()

    # agent_process_queue = AgentProcessQueue()
    
    executor = Executor(agent_factory)

    scheduler = FIFOScheduler(llm)

    scheduler.run()
    
    while True:
        instruction = input("[{}] AIOS>".format(llm_type)).strip()
        parsed_command = parser.parse(instruction)
        executor.execute(parsed_command)

if __name__ == "__main__":
    main()
