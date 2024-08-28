import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


import warnings
from dotenv import load_dotenv
from aios.sdk.interpreter.adapter import prepare_interpreter
from aios.hooks.llm import useKernel, useFIFOScheduler
from aios.utils.utils import delete_directories
from aios.utils.utils import (
    parse_global_args,
)
from pyopenagi.agents.agent_process import AgentProcessFactory

from interpreter import interpreter


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

    prepare_interpreter(process_factory)

    startScheduler()

    # interpreter.chat("Calculate 10 * 20 / 2")
    # interpreter.chat("Plot the sin function")
    # interpreter.chat("Use the Euclidean algorithm to calculate the greatest common divisor (GCD) of 78782 and 64.")
    interpreter.chat("In a group of 23 people, the probability of at least two having the same birthday is greater than 50%")

    stopScheduler()

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
