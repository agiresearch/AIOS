# This is a main script that tests the functionality of specific agents.
# It requires no user input.
import warnings
from dotenv import load_dotenv

from aios.community import prepare_framework, FrameworkType
from aios.hooks.llm import aios_starter
from aios.utils import delete_directories
from aios.utils import (
    parse_global_args,
)
from autogen import ConversableAgent
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
    load_dotenv()

    with aios_starter(**vars(args)):

        prepare_framework(FrameworkType.AutoGen)

        # Let's first define the assistant agent that suggests tool calls.
        assistant = ConversableAgent(
            name="Assistant",
            system_message="You are a helpful AI assistant. "
                           "You can help with simple calculations. "
                           "Return 'TERMINATE' when the task is done."
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

        # Generate a reply.
        chat_result = user_proxy.initiate_chat(assistant, message="What is  (2 + 1) / 3?")

        print(chat_result)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
