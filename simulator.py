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

from src.scheduler.rr_scheduler import RRScheduler

from src.utils.utils import (
    parse_global_args,
)

from src.agents.agent_factory import AgentFactory

from src.agents.agent_process import AgentProcessFactory

import warnings

from src.llm_kernel import llms

import threading

terminate_signal = threading.Event()

def main():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode

    llm = llms.LLMKernel(
        llm_name,
        max_gpu_memory,
        eval_device,
        max_new_tokens
    )

    # start the scheduler
    # scheduler = FIFOScheduler(
    #     llm = llm,
    #     log_mode = scheduler_log_mode
    # )

    scheduler = RRScheduler(
        llm = llm,
        log_mode = scheduler_log_mode
    )

    agent_process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue,
        agent_process_factory = agent_process_factory,
        agent_log_mode = agent_log_mode
    )

    parser = PunctuationParser(
        llm = llm
    )

    executor = Executor(agent_factory=agent_factory)

    scheduler.start()

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

    scheduler.stop()

if __name__ == "__main__":
    main()
