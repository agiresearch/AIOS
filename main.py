import os
import sys
import json
# from src.command_parser import (
#     PunctuationParser,
#     ChatGPTParser
# )

# from src.command_executor import (
#     Executor
# )

from src.scheduler.fifo_scheduler import FIFOScheduler

from src.utils.utils import parse_global_args

import warnings

# from src.agent_factory import (
#     AgentFactory
# )

from src.llms import llms

from src.agents.math_agent.math_agent import MathAgent

from src.agents.narrative_agent.narrative_agent import NarrativeAgent

from src.agents.rec_agent.rec_agent import RecAgent

from src.agents.travel_agent.travel_agent import TravelAgent

from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    warnings.filterwarnings("ignore")
    parser = parse_global_args()
    args = parser.parse_args()

    llm_name = args.llm_name
    max_gpu_memory = args.max_gpu_memory
    max_new_tokens = args.max_new_tokens

    llm = llms.LLMKernel(llm_name, max_gpu_memory, max_new_tokens)

    scheduler = FIFOScheduler(llm)

    scheduler.start()

    # assign maximum number of agents that can run in parallel
    agent_thread_pool = ThreadPoolExecutor(max_workers=64)

    math_agent = MathAgent(
        agent_name = "MathAgent", 
        task_input = "Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?",
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue
    )

    narrative_agent = NarrativeAgent(
        agent_name = "NarrativeAgent", 
        task_input = "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island.",
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue
    )

    rec_agent = RecAgent(
        agent_name = "RecAgent", 
        task_input = "I want to take a tour to New York during the spring break, recommend some restaurants around for me.",
        llm = llm,
        agent_process_queue = scheduler.agent_process_queue
    )

    agents = [math_agent, narrative_agent, rec_agent]

    tasks = [agent_thread_pool.submit(agent.run) for agent in agents]

    for r in as_completed(tasks):
        res = r.result()
        print(res)

    scheduler.stop()

if __name__ == "__main__":
    main()
