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
from pyopenagi.agents.agent_process import AgentProcessFactory

from autogen import ConversableAgent, UserProxyAgent


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

    prepare_autogen(process_factory)

    # Create the agent that uses the LLM.
    assistant = ConversableAgent("agent", agent_process_factory=process_factory)

    # Create the agent that represents the user in the conversation.
    user_proxy = UserProxyAgent("user", code_execution_config=False)

    startScheduler()

    # Let the assistant start the conversation.  It will end when the user types exit.
    assistant.initiate_chat(user_proxy, message="How can I help you today?")

    stopScheduler()

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
