import os
import sys

# from src.command_parser import (
#     PunctuationParser,
#     ChatGPTParser
# )

# from src.command_executor import (
#     Executor
# )

from src.scheduler.fifo_scheduler import FIFOScheduler

import warnings

# from src.agent_factory import (
#     AgentFactory
# )

from src.llms import llms

# from src.agents.agent_process import (
#     AgentProcess,
#     AgentProcessQueue
# )

from src.agents.math_agent import MathAgent

from src.agents.narrative_agent import NarrativeAgent

from src.agents.rec_agent import RecAgent

from concurrent.futures import ThreadPoolExecutor, as_completed

# os.environ["CUDA_VISIBLE_DEVICES"] = "4,5,6,7"

def main():
    warnings.filterwarnings("ignore")
    # agent_process_queue.print()
    # llm_type = "llama2-13b-chat-hf"
    llm_type = "gemma-2b-it"
    # llm_type = "gemma-7b-it"

    llm = llms.LLMKernel(llm_type)

    # parser = PunctuationParser(llm)

    # agent_factory = AgentFactory()

    # agent_thread_pool to enable multiple agents running in parallel
    agent_thread_pool = ThreadPoolExecutor(max_workers=64)

    # agent_process_queue to submit agent requests
    agent_process_queue = ThreadPoolExecutor(max_workers=1)

    math_agent = MathAgent(
        "MathAgent", 
        "Solve the problem that Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?",
        llm,
        agent_process_queue
    )

    narrative_agent = NarrativeAgent(
        "NarrativeAgent", 
        "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island.",
        llm,
        agent_process_queue
    )

    rec_agent = RecAgent(
        "RecAgent", 
        "I want to take a tour to New York during the spring break, recommend some restaurants around for me.",
        llm,
        agent_process_queue
    )
    agents = [math_agent, narrative_agent, rec_agent]
    tasks = [agent_thread_pool.submit(a.run) for a in agents]

    for r in as_completed(tasks):
        res = r.result()
        print(res)

if __name__ == "__main__":
    main()
