# This is a main script that tests the functionality of specific agents.
# It requires no user input.
import tempfile
import warnings
from dotenv import load_dotenv

from aios.sdk import FrameworkType, prepare_framework
from aios.hooks.llm import aios_starter
from aios.utils.utils import delete_directories
from aios.utils.utils import (
    parse_global_args,
)
from autogen import ConversableAgent
from autogen.coding import LocalCommandLineCodeExecutor


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
        # Create a temporary directory to store the code files.
        temp_dir = tempfile.TemporaryDirectory()

        # Create a local command line code executor.
        executor = LocalCommandLineCodeExecutor(
            timeout=10,  # Timeout for each code execution in seconds.
            work_dir=temp_dir.name,  # Use the temporary directory to store the code files.
        )

        # Create an agent with code executor configuration.
        code_executor_agent = ConversableAgent(
            "code_executor_agent",
            code_execution_config={"executor": executor},  # Use the local command line code executor.
            human_input_mode="ALWAYS",  # Always take human input for this agent for safety.
        )

        prepare_framework(FrameworkType.AutoGen)

        message_with_code_block = """This is a message with code block.
        The code block is below:
        ```python
import numpy as np
import matplotlib.pyplot as plt
x = np.random.randint(0, 100, 100)
y = np.random.randint(0, 100, 100)
plt.scatter(x, y)
plt.savefig('scatter.png')
print('Scatter plot saved to scatter.png')
        ```
        This is the end of the message.
        """

        # Generate a reply for the given code.
        reply = code_executor_agent.generate_reply(messages=[{"role": "user", "content": message_with_code_block}])
        temp_dir.cleanup()

        print(reply)

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
