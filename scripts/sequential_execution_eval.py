import os
import sys
import json

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.scheduler.rr_scheduler import RRScheduler

from src.utils.utils import (
    parse_global_args,
)

from src.agents.agent_factory import AgentFactory

from src.agents.agent_process import AgentProcessFactory

import warnings

from src.llm_kernel import llms

from concurrent.futures import ThreadPoolExecutor, as_completed

from multiprocessing import Process

from src.utils.utils import delete_directories

def clean_cache(root_directory):
    targets = {'.ipynb_checkpoints', '__pycache__', ".pytest_cache", "context_restoration"}
    delete_directories(root_directory, targets)

def sequential_execution():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    agent_log_mode = args.agent_log_mode
    llm_kernel_log_mode = args.llm_kernel_log_mode

    llm = llms.LLMKernel(
        llm_name = llm_name,
        max_gpu_memory = max_gpu_memory,
        eval_device = eval_device,
        max_new_tokens = max_new_tokens,
        log_mode = llm_kernel_log_mode
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

    scheduler.start()
    agents = [
        ["MathAgent", "Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?"],
        ["NarrativeAgent", "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."],
        ["RecAgent", "I want to take a tour to New York during the spring break, recommend some restaurants around for me."]
    ]

    sequential_execution_stats = []

    accumulated_time = 0
    for agent_name, task_input in agents:
        output = agent_factory.run_agent(
            agent_name=agent_name,
            task_input=task_input
        )
        agent_name = output["agent_name"]
        execution_time = output["execution_time"]
        avg_waiting_time = output["avg_waiting_time"]
        avg_turnaround_time = output["avg_turnaround_time"]
        rounds = output["rounds"]

        avg_waiting_time += accumulated_time / rounds
        avg_turnaround_time += accumulated_time / rounds

        accumulated_time += execution_time

        sequential_execution_stats.append([agent_name, avg_waiting_time, avg_turnaround_time])

    print("**** Sequential Execution Statistics Starts ****")

    for agent_name, avg_waiting_time, avg_turnaround_time in sequential_execution_stats:
        print(f"{agent_name}'s avg waiting time is {avg_waiting_time}, avg turnaround time is {avg_turnaround_time}.")

    print("**** Sequential Execution Statistics Ends ****\n")

    clean_cache(root_directory="./")

    scheduler.stop()

def main():
    sequential_execution()

if __name__ == "__main__":
    main()
