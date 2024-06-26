# This file is used to evaluate the configuration passed through arguments to the simulation of the kernel

import json

from aios.scheduler.fifo_scheduler import FIFOScheduler


from pyopenagi.agents.agent_factory import AgentFactory

from pyopenagi.agents.agent_process import AgentProcessFactory

import warnings

from aios.llm_kernel import llms

from concurrent.futures import ThreadPoolExecutor


from aios.utils.utils import delete_directories
from aios.utils.calculator import get_numbers_concurrent, get_numbers_sequential, comparison

import argparse


from dotenv import load_dotenv

# Construct help message and parse argumets using argparse
def parse_global_args():
    """ parser in aios/utils/utils.py with --agents and --agent-log-mode argument """
    parser = argparse.ArgumentParser(description="Parse global parameters")
    parser.add_argument('--llm_name', type=str, default="gemma-2b-it", help="Specify the LLM name of AIOS")
    parser.add_argument('--max_gpu_memory', type=json.loads, help="Max gpu memory allocated for the LLM")
    parser.add_argument('--eval_device', type=str, help="Evaluation device (example: \"conda:0\" for 2 GPUs)")
    parser.add_argument('--max_new_tokens', type=int, default=256,
                        help="The maximum number of new tokens for generation")
    parser.add_argument("--scheduler_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--agent_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--mode", type=str, default="compare", choices=["compare", "concurrent-only", "sequential-only"])
    parser.add_argument("--llm_kernel_log_mode", type=str, default="console", choices=["console", "file"])
    parser.add_argument("--agents", type=str, required=True,
                        help="following the format of <agent1>:<agent1_num>,<agent2>:<agent2_num>")

    return parser


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

    llm = llms.LLMKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode
    )

    scheduler = FIFOScheduler(
        llm=llm,
        log_mode=scheduler_log_mode
    )

    agent_process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        llm=llm,
        agent_process_queue=scheduler.agent_process_queue,
        agent_process_factory=agent_process_factory,
        agent_log_mode=agent_log_mode
    )

    agent_thread_pool = ThreadPoolExecutor(max_workers=2000)

    scheduler.start()

    agents = args.agents
    agent_list = []
    for agent in agents.split(","):
        agent = agent.split(":")
        agent_name = agent[0]
        agent_num = int(agent[1])
        agent_list.append((agent_name, agent_num))

    def execute_mode(mode, agent_list, agent_factory, agent_thread_pool=None):
        print(f"**** {mode} Execution Statistics Starts ****\n")
        if mode == "concurrent":
            metrics = get_numbers_concurrent(agent_list, agent_factory, agent_thread_pool)
        else:
            metrics = get_numbers_sequential(agent_list, agent_factory)
        print(f"{mode.capitalize()} Metrics:", metrics)
        print(f"**** {mode} Execution Statistics Ends ****\n")
        return metrics

    if args.mode == "compare":
        concurrent_metrics = execute_mode("concurrent", agent_list, agent_factory, agent_thread_pool)
        sequential_metrics = execute_mode("sequential", agent_list, agent_factory)
        comparison(concurrent_metrics, sequential_metrics)
    elif args.mode == "concurrent-only":
        execute_mode("concurrent", agent_list, agent_factory, agent_thread_pool)
    elif args.mode == "sequential-only":
        execute_mode("sequential", agent_list, agent_factory)
    else:
        print("Error: Invalid mode")

    clean_cache(root_directory="./")

    scheduler.stop()


if __name__ == "__main__":
    main()
