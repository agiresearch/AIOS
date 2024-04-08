import os
import sys
import json

from src.command_parser import (
    PunctuationParser,
    ChatGPTParser
)

from src.command_executor import (
    Executor
)

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.utils.utils import (
    parse_global_args,
    # logger
)

from src.agents.agent_factory import AgentFactory

import warnings

from src.llms import llms

from src.agents.math_agent.math_agent import MathAgent

from src.agents.narrative_agent.narrative_agent import NarrativeAgent

from src.agents.rec_agent.rec_agent import RecAgent

from src.agents.travel_agent.travel_agent import TravelAgent

from concurrent.futures import ThreadPoolExecutor, as_completed

import threading

terminate_signal = threading.Event()

def main():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode

    llm = llms.LLMKernel(llm_name, max_gpu_memory, max_new_tokens)

    # start the scheduler
    scheduler = FIFOScheduler(
        llm = llm,
        log_mode = scheduler_log_mode
    )

    agent_factory = AgentFactory(
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue,
        agent_log_mode = agent_log_mode
    )

    parser = PunctuationParser(
        llm = llm
    )

    executor = Executor(agent_factory=agent_factory)

    scheduler.start()

    agent_factory.start() # TODO add garbage recycle of agent ID

    while True:
        try:
            # Read a command line input
            command_line = input(f"[{llm_name}]>")
            if command_line.strip().lower() == "exit":
                print("Exiting...")
                # agent_factory.terminate_signal.set()
                break

            # Parse command
            tokens = parser.parse(command_line)
            # Execute the command
            executor.execute(tokens)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nUse 'exit' to quit the shell.")
        except EOFError:
            pass

    agent_factory.terminate_signal.set()

    agent_factory.stop()
    scheduler.stop()

if __name__ == "__main__":
    main()
