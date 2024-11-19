#!/usr/bin/env python3
import os
import sys
import warnings
import asyncio
from aios.utils.utils import (
    parse_global_args,
    delete_directories
)
from aios.hooks.starter import aios_starter
from dotenv import load_dotenv

# Add AIOS path
aios_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, aios_root)


def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def main():
    main_id = os.getpid()
    print(f"Main ID is: {main_id}")
    warnings.filterwarnings("ignore")
    # Use global argument parser
    parser = parse_global_args()
    parser.add_argument('--task', type=str, required=True, help='Task description for SeeAct')
    args = parser.parse_args()
    load_dotenv()
    # Extract task from arguments
    args_dict = vars(args)
    task = args_dict.pop('task')  # Remove task parameter
    with aios_starter(**args_dict) as (submit_agent, await_agent_execution):
        agent_tasks = [
            [
                "example/seeact_agent",
                task,
                {
                    "model": "gpt-4o",
                    "default_website": "https://www.google.com/",
                    "headless": True
                }
            ]
        ]
        agent_ids = []
        for task in agent_tasks:
            agent_name = task[0]
            task_input = task[1]
            config = task[2] if len(task) > 2 else {}
            agent_id = submit_agent(
                agent_name=agent_name,
                task_input=task_input,
                **config
            )
            agent_ids.append(agent_id)

        for agent_id in agent_ids:
            result = await_agent_execution(agent_id)
            if asyncio.iscoroutine(result):
                loop = asyncio.get_event_loop()
                result = loop.run_until_complete(result)
            print(f"Task result: {result}")

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
