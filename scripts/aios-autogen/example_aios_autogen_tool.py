# This is a main script that tests the functionality of specific agents.
# It requires no user input.
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import warnings
from dotenv import load_dotenv
from aios.sdk.autogen.adapter import prepare_autogen
from aios.hooks.llm import useKernel, useFIFOScheduler
from aios.utils.utils import delete_directories
from aios.utils.utils import (
    parse_global_args,
)
from autogen import ConversableAgent
from pyopenagi.agents.agent_process import AgentProcessFactory
from typing import Annotated, Literal

Operator = Literal["+", "-", "*", "/"]

def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def calculator(a: int, b: int, operator: Annotated[Operator, "operator"]) -> int:
    if operator == "+":
        return a + b
    elif operator == "-":
        return a - b
    elif operator == "*":
        return a * b
    elif operator == "/":
        return int(a / b)
    else:
        raise ValueError("Invalid operator")


def main():
    # parse arguments and set configuration for this run accordingly
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    eval_device = args.eval_device
    max_new_tokens = args.max_new_tokens
    scheduler_log_mode = args.scheduler_log_mode
    # agent_log_mode = args.agent_log_mode
    llm_kernel_log_mode = args.llm_kernel_log_mode
    use_backend = args.use_backend
    load_dotenv()

    llm = useKernel(
        llm_name=llm_name,
        max_gpu_memory=max_gpu_memory,
        eval_device=eval_device,
        max_new_tokens=max_new_tokens,
        log_mode=llm_kernel_log_mode,
        use_backend=use_backend
    )

    # run agents concurrently for maximum efficiency using a scheduler

    # scheduler = FIFOScheduler(llm=llm, log_mode=scheduler_log_mode)

    startScheduler, stopScheduler = useFIFOScheduler(
        llm=llm,
        log_mode=scheduler_log_mode,
        get_queue_message=None
    )

    process_factory = AgentProcessFactory()

    prepare_autogen()

    # Let's first define the assistant agent that suggests tool calls.
    assistant = ConversableAgent(
        name="Assistant",
        system_message="You are a helpful AI assistant. "
                       "You can help with simple calculations. "
                       "Return 'TERMINATE' when the task is done.",
        agent_process_factory = process_factory
    )

    # The user proxy agent is used for interacting with the assistant agent
    # and executes tool calls.
    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
    )

    # Register the tool signature with the assistant agent.
    assistant.register_for_llm(name="calculator", description="A simple calculator")(calculator)

    # Register the tool function with the user proxy agent.
    user_proxy.register_for_execution(name="calculator")(calculator)

    startScheduler()

    # Generate a reply.
    chat_result = user_proxy.initiate_chat(assistant, message="What is  (2 + 1) / 3?")

    stopScheduler()

    print(chat_result)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
