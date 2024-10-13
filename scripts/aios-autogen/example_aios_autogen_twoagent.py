# This is a main script that tests the functionality of specific agents.
# It requires no user input.
import warnings
from dotenv import load_dotenv

from aios.sdk import FrameworkType, prepare_framework
from aios.hooks.llm import aios_starter
from aios.utils.utils import delete_directories
from aios.utils.utils import (
    parse_global_args,
)
from autogen import ConversableAgent


def clean_cache(root_directory):
    targets = {
        ".ipynb_checkpoints",
        "__pycache__",
        ".pytest_cache",
        "context_restoration",
    }
    delete_directories(root_directory, targets)


def main():
    # parse arguments and set configuration for this run accordingly
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()
    load_dotenv()

    with aios_starter(**vars(args)):

        prepare_framework(FrameworkType.AutoGen)

        cathy = ConversableAgent(
            "cathy",
            system_message="Your name is Cathy and you are a part of a duo of comedians.",
            human_input_mode="NEVER",  # Never ask for human input.
        )

        joe = ConversableAgent(
            "joe",
            system_message="Your name is Joe and you are a part of a duo of comedians.",
            human_input_mode="NEVER",  # Never ask for human input.
        )

        # Let the assistant start the conversation.  It will end when the user types exit.
        result = joe.initiate_chat(cathy, message="How can I help you today?", max_turns=2)

        print(result)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
