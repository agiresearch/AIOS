import os
import sys
import json

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.scheduler.rr_scheduler import RRScheduler

from src.utils.utils import (
    parse_global_args,
)

from openagi.src.agents.agent_factory import AgentFactory

# from openagi.src.agents.agent_process import AgentProcessFactory

import warnings

from src.llm_kernel import llms

# from concurrent.futures import ThreadPoolExecutor, as_completed
from concurrent.futures import ProcessPoolExecutor, as_completed

import multiprocessing

import psutil

import threading

import queue

from src.utils.utils import delete_directories
from dotenv import find_dotenv, load_dotenv

def clean_cache(root_directory):
    targets = {'.ipynb_checkpoints', '__pycache__', ".pytest_cache", "context_restoration"}
    delete_directories(root_directory, targets)

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
    load_dotenv()

    agent_process_queue = multiprocessing.Queue()
    # agent_process_queue = queue.Queue()

    llm_request_responses = multiprocessing.Manager().dict()
    # llm_request_responses = dict()

    llm_request_responses = multiprocessing.Manager().dict()

    llm = llms.LLMKernel(
        llm_name = llm_name,
        max_gpu_memory = max_gpu_memory,
        eval_device = eval_device,
        max_new_tokens = max_new_tokens,
        log_mode = llm_kernel_log_mode
    )

    scheduler = FIFOScheduler(
        llm = llm,
        agent_process_queue = agent_process_queue,
        llm_request_responses = llm_request_responses,
        log_mode = scheduler_log_mode
    )

    # scheduler_process = psutil.Process(scheduler.pid)
    # print(f"Scheduler running on CPU:", scheduler_process.cpu_num())
    # print(multiprocessing.cpu_count())

    agent_factory = AgentFactory(
        llm = llm,
        agent_process_queue = agent_process_queue,
        llm_request_responses = llm_request_responses,
        agent_log_mode = agent_log_mode
    )

    # print(scheduler.cpu_affinity())

    scheduler.start()

    agent_a = agent_factory.activate_agent(
        agent_name = "MathAgent",
        task_input = "Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?"
    )

    agent_a.start()

    agent_b = agent_factory.activate_agent(
        agent_name = "MathAgent",
        task_input = "Mark has 4 bags of marbles, each with 25 marbles. He gives 3 marbles to each of his 5 friends. How many marbles does he have left?"
    )

    agent_b.start()

    agent_a.join()

    agent_b.join()

    # rec_agent = agent_factory.run_agent(
    #     agent_name = "RecAgent",
    #     task_input = "I want to take a tour to New York during the spring break, recommend some restaurants around for me."
    # )

    # agent_tasks = [math_agent, rec_agent]

    # for agent_task in agent_tasks:
    #     agent_task.start()
    # math_agent.start()


    # math_agent.join()
    # agent_thread_pool = ThreadPoolExecutor(max_workers=64)
    # agent_thread_pool = ProcessPoolExecutor(max_workers=64)


    # # construct agents
    # math_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "MathAgent",
    #     "Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?"
    # )

    # narrative_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "NarrativeAgent",
    #     "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
    # )

    # rec_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "RecAgent", "I want to take a tour to New York during the spring break, recommend some restaurants around for me."
    # )

    # agent_tasks = [math_agent, narrative_agent, rec_agent]

    # for r in as_completed(agent_tasks):
    #     res = r.result()

    # scheduler.join()

    # scheduler.stop()
    scheduler.terminate()

    clean_cache(root_directory="./")

if __name__ == "__main__":
    main()
