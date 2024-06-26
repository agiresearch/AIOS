# This simulates AIOS as an LLM kernel, although it is only acting as a userspace
# wrapper in this script.


from aios.command_parser import (
    PunctuationParser,
    ChatGPTParser
)

from aios.command_executor import (
    Executor
)

from aios.scheduler.fifo_scheduler import FIFOScheduler


from aios.utils.utils import (
    parse_global_args,
)

from pyopenagi.agents.agent_factory import AgentFactory

from pyopenagi.agents.agent_process import AgentProcessFactory

import warnings

from aios.llm_kernel import llms


from aios.utils.utils import delete_directories
from dotenv import load_dotenv

def clean_cache(root_directory):
    targets = {'.ipynb_checkpoints', '__pycache__', ".pytest_cache", "context_restoration"}
    delete_directories(root_directory, targets)

def main():
    # parse arguments into configuration for this runtime
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
        llm_name = llm_name,
        max_gpu_memory = max_gpu_memory,
        eval_device = eval_device,
        max_new_tokens = max_new_tokens,
        log_mode = llm_kernel_log_mode
    )

    # allow agents to execute concurrently using a simple scheduler
    scheduler = FIFOScheduler(
        llm = llm,
        log_mode = scheduler_log_mode
    )

    agent_process_factory = AgentProcessFactory()

    agent_factory = AgentFactory(
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue,
        agent_process_factory = agent_process_factory,
        agent_log_mode = agent_log_mode
    )

    parser = PunctuationParser(
        llm = llm
    )

    executor = Executor(agent_factory=agent_factory)

    scheduler.start()

    # run commands indefinitely, parsing from command_executor.py
    while True:
        try:
            # Read a command line input
            command_line = input(f"[{llm_name}]>")
            if command_line.strip().lower() == "exit":
                print("Exiting...")
                # agent_factory.terminate_signal.set()
                break

            # Parse command
            tokens = parser.parse(command_line)
            # Execute the command
            executor.execute(tokens)

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nUse 'exit' to quit the shell.")
        except EOFError:
            pass

    scheduler.stop()

    clean_cache("./")

if __name__ == "__main__":
    main()
