import os
import sys
import json

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.scheduler.rr_scheduler import RRScheduler

from openagi.src.agents.agent_factory import AgentFactory

from openagi.src.agents.agent_process import AgentProcessFactory

import warnings

from src.llm_kernel import llms

from concurrent.futures import ThreadPoolExecutor, as_completed

from multiprocessing import Process

from src.utils.utils import delete_directories

import argparse

import random

import numpy as np

def parse_global_args():
    parser = argparse.ArgumentParser(description="Parse global parameters")
    parser.add_argument('--llm_name', type=str, default="gemma-2b-it", help="Specify the LLM name of AIOS")
    parser.add_argument('--max_gpu_memory', type=json.loads, help="Max gpu memory allocated for the LLM")
    parser.add_argument('--eval_device', type=str, help="Evaluation device")
    parser.add_argument('--max_new_tokens', type=int, default=256, help="The maximum number of new tokens for generation")
    parser.add_argument("--scheduler_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--agent_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--llm_kernel_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--agents", type=str, required=True,
                        help="following the format of <agent1>:<agent1_num>,<agent2>:<agent2_num>")

    return parser

def clean_cache(root_directory):
    targets = {'.ipynb_checkpoints', '__pycache__', ".pytest_cache", "context_restoration"}
    delete_directories(root_directory, targets)

def load_agent_tasks(agent_name):
    file_path = os.path.join(os.getcwd(), "scripts", f"{agent_name}_task.txt")
    with open(file_path) as f:
        task_inputs = f.readlines()
        return task_inputs

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
    llm_kernel_log_mode = args.llm_kernel_log_mode

    llm = llms.LLMKernel(
        llm_name = llm_name,
        max_gpu_memory = max_gpu_memory,
        eval_device = eval_device,
        max_new_tokens = max_new_tokens,
        log_mode = llm_kernel_log_mode
    )

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

    agent_thread_pool = ThreadPoolExecutor(max_workers=2000)

    scheduler.start()

    agents = args.agents

    agent_tasks = []

    agent_list = []

    for agent in agents.split(","):
        agent = agent.split(":")
        agent_name = agent[0]
        agent_num = int(agent[1])
        agent_list.append((agent_name, agent_num))

    for agent_name, agent_num in agent_list:
        task_input = load_agent_tasks(agent_name=agent_name)[0]
        for i in range(agent_num):
            agent_task = agent_thread_pool.submit(
                agent_factory.run_agent,
                agent_name,
                task_input
            )
            agent_tasks.append(agent_task)

    concurrent_execution_stats = []

    for r in as_completed(agent_tasks):
        output = r.result()
        agent_name = output["agent_name"]
        execution_time = output["execution_time"]
        avg_waiting_time = output["avg_waiting_time"]
        avg_turnaround_time = output["avg_turnaround_time"]

        concurrent_execution_stats.append([avg_waiting_time, avg_turnaround_time])

    print("**** Concurrent Execution Statistics Starts ****")

    avg_concurrent_execution_stats = np.mean(np.array(concurrent_execution_stats), axis=0)

    print(f"Average waiting time: {avg_concurrent_execution_stats[0]}, Average turnaround time: {avg_concurrent_execution_stats[1]}")

    print("**** Concurrent Execution Statistics Ends ****\n")

    sequential_execution_stats = []

    accumulated_time = 0
    for agent_name, agent_num in agent_list:
        task_input = load_agent_tasks(agent_name=agent_name)[0]
        for i in range(agent_num):
            agent_tasks.append(agent_task)
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

            sequential_execution_stats.append([avg_waiting_time, avg_turnaround_time])

    print("**** Sequential Execution Statistics Starts ****")

    avg_sequential_execution_stats = np.mean(np.array(sequential_execution_stats), axis=0)

    print(f"Average waiting time: {avg_sequential_execution_stats[0]}, Average turnaround time: {avg_sequential_execution_stats[1]}")

    print("**** Sequential Execution Statistics Ends ****\n")

    print("**** Improvement Analysis Starts ****")

    waiting_time_improv = (avg_sequential_execution_stats[0] - avg_concurrent_execution_stats[0]) / avg_sequential_execution_stats[0]
    turnaround_time_improv = (avg_sequential_execution_stats[1] - avg_concurrent_execution_stats[1]) / avg_sequential_execution_stats[1]
    print(f"Improvement of waiting time: {waiting_time_improv * 100:.2f}%")
    print(f"Improvement of turnaround time: {turnaround_time_improv * 100:.2f}%")
    print("**** Improvement Analysis Ends ****")

    clean_cache(root_directory="./")

    scheduler.stop()

if __name__ == "__main__":
    main()
