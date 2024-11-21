from aios.utils.utils import (
    parse_global_args,
)
import os
import warnings

from aios.hooks.starter import aios_starter

from aios.utils.utils import delete_directories
from dotenv import load_dotenv

from typing import Tuple, Callable, Dict, Any
from aios.hooks.modules.llm import useCore
from aios.hooks.modules.memory import useMemoryManager
from aios.hooks.modules.storage import useStorageManager
from aios.hooks.modules.tool import useToolManager
from aios.hooks.modules.agent import useFactory
from aios.hooks.modules.scheduler import fifo_scheduler_nonblock as fifo_scheduler

class AIOSStarter:
    def __init__(
        self,
        llm_name: str,
        max_gpu_memory: str,
        eval_device: str,
        max_new_tokens: int,
        scheduler_log_mode: str,
        agent_log_mode: str,
        llm_core_log_mode: str,
        use_backend: str,
    ):
        """
        Initializes components for running agents with an LLM kernel and scheduler.

        Args:
            llm_name (str): The name of the LLM kernel to use.
            max_gpu_memory (str): The maximum amount of GPU memory to use.
            eval_device (str): The device to evaluate the LLM on.
            max_new_tokens (int): The maximum number of new tokens to generate.
            scheduler_log_mode (str): The log mode for the scheduler.
            agent_log_mode (str): The log mode for the agents.
            llm_core_log_mode (str): The log mode for the LLM kernel.
            use_backend (str): The backend to use for running the LLM kernel.
        """
        # Initialize LLM
        self.llm = useCore(
            llm_name=llm_name,
            max_gpu_memory=max_gpu_memory,
            eval_device=eval_device,
            max_new_tokens=max_new_tokens,
            log_mode=llm_core_log_mode,
            use_backend=use_backend,
        )

        # Initialize storage manager
        self.storage_manager = useStorageManager(
            root_dir="root",
            use_vector_db=False
        )
        
        # Initialize memory manager
        self.memory_manager = useMemoryManager(
            memory_limit=100*1024*1024,
            eviction_k=10,
            storage_manager=self.storage_manager
        )

        # Initialize tool manager
        self.tool_manager = useToolManager()

        # Initialize agent factory
        self.submit_agent, self.await_agent_execution = useFactory(
            log_mode=agent_log_mode, max_workers=64
        )

        # Initialize scheduler
        self.scheduler = fifo_scheduler(
            llm=self.llm,
            memory_manager=self.memory_manager,
            storage_manager=self.storage_manager,
            tool_manager=self.tool_manager,
            log_mode=scheduler_log_mode,
            get_llm_syscall=None,
            get_memory_syscall=None,
            get_storage_syscall=None,
            get_tool_syscall=None
        )

    def start(self) -> Tuple[Callable[[str, str], int], Callable[[str], Dict[str, Any]]]:
        """
        Starts the scheduler and returns agent submission and execution functions.

        Returns:
            Tuple: A tuple containing the submitAgent and awaitAgentExecution functions.
        """
        self.scheduler.start()
        return self.submit_agent, self.await_agent_execution

    def stop(self):
        """
        Stops the scheduler and cleans up resources.
        """
        self.scheduler.stop()

# Example usage:
"""
# Initialize
aios = AIOSStarter(
    llm_name="gpt-3.5-turbo",
    max_gpu_memory="12GiB",
    eval_device="cuda",
    max_new_tokens=512,
    scheduler_log_mode="info",
    agent_log_mode="info",
    llm_core_log_mode="info",
    use_backend="transformers"
)

# Start and get functions
submit_agent, await_agent_execution = aios.start()

try:
    # Use the functions
    task_id = submit_agent("some_task", {"param": "value"})
    result = await_agent_execution(task_id)
finally:
    # Clean up
    aios.stop()
"""

main_id = os.getpid()
print(f"Main ID is: {main_id}")
warnings.filterwarnings("ignore")
parser = parse_global_args()
args = parser.parse_args()
load_dotenv()

aios = AIOSStarter(**vars(args))

# Start and get functions
submit_agent, await_agent_execution = aios.start()

try:
    # Use the functions
    task_id = submit_agent(agent_name="example/academic_agent", task_input="Tell me what is the prollm paper mainly about? ")
    result = await_agent_execution(task_id)
finally:
    # Clean up
    aios.stop()


