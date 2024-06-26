# This is a main script that tests the functionality of specific agents.
# It requires no user input.


from aios.scheduler.fifo_scheduler import FIFOScheduler


from aios.utils.utils import (
    parse_global_args,
)

from pyopenagi.agents.agent_factory import AgentFactory

from pyopenagi.agents.agent_process import AgentProcessFactory

import warnings

from aios.llm_kernel import llms

from concurrent.futures import ThreadPoolExecutor, as_completed


from aios.utils.utils import delete_directories
from dotenv import find_dotenv, load_dotenv

def clean_cache(root_directory):
    targets = {'.ipynb_checkpoints', '__pycache__', ".pytest_cache", "context_restoration"}
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
    agent_log_mode = args.agent_log_mode
    llm_kernel_log_mode = args.llm_kernel_log_mode
    _use_backend = args.use_backend
    load_dotenv()

    llm = llms.LLMKernel(
        llm_name = llm_name,
        max_gpu_memory = max_gpu_memory,
        eval_device = eval_device,
        max_new_tokens = max_new_tokens,
        log_mode = llm_kernel_log_mode,
        use_backend = args.use_backend
    )

    # run agents concurrently for maximum efficiency using a scheduler

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

    agent_thread_pool = ThreadPoolExecutor(max_workers=500)

    scheduler.start()

    # construct example agents

    # travel_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "TravelAgent", "I want to take a trip to Paris, France from July 4th to July 10th 2024 and I am traveling from New York City. Help me plan this trip."
    # )

    # math_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "MathAgent",
    #     "Convert 15000 MXN to Canadian Dollars and find out how much it would be in USD if 1 CAD equals 0.79 USD."
    # )

    academic_agent = agent_thread_pool.submit(
        agent_factory.run_agent,
        "AcademicAgent",
        "Summarize recent advancements in quantum computing from the past five years."
    )

    # rec_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "RecAgent", "Recommend two movies with groundbreaking visual effects released in the last fifteen years ranked between 1 and 20 with ratings above 8.0."
    # )

    # creation_agent = agent_thread_pool.submit(
    #     agent_factory.run_agent,
    #     "CreationAgent", "Create an image of a lush jungle with an ancient temple, evoking a sense of mystery and adventure."
    # )

    # agent_tasks = [travel_agent, rec_agent, creation_agent, math_agent, academic_agent]
    # agent_tasks = [rec_agent]
    # agent_tasks = [creation_agent]
    agent_tasks = [academic_agent]

    for r in as_completed(agent_tasks):
        _res = r.result()

    scheduler.stop()

    clean_cache(root_directory="./")

if __name__ == "__main__":
    main()
