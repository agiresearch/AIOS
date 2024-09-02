import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import warnings
from aios.sdk.metagpt.adapter import prepare_metagpt
from dotenv import load_dotenv
from aios.hooks.llm import useKernel, useFIFOScheduler
from aios.utils.utils import (
    parse_global_args,
    delete_directories
)
from pyopenagi.agents.agent_process import AgentProcessFactory
import asyncio
from metagpt.roles.di.data_interpreter import DataInterpreter

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

    prepare_metagpt(process_factory)

    startScheduler()

    async def main():
        di = DataInterpreter()
        await di.run("Run data analysis on sklearn Iris dataset, include a plot")

    asyncio.run(main())  # or await main() in a jupyter notebook setting

    stopScheduler()

    clean_cache(root_directory="./")


if __name__ == "__main__":
    main()
