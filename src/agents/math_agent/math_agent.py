# from src.agents.base import BaseAgent

from src.agents.base import BaseAgent

import os

import time

import sys

from src.agents.agent_process import (
    AgentProcess
)

from src.utils.global_param import (
    agent_pool,
)

from src.utils.utils import (
    logger
)

import argparse

from concurrent.futures import as_completed

import numpy as np

class MathAgent(BaseAgent):
    def __init__(self, agent_name, task_input, llm, agent_process_queue):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue)
        
    
    def run(self):
        prompt = ""
        prefix = self.prefix
        task_input = self.task_input
        prompt += prefix
        waiting_times = []
        turnaround_times = []
        task_input = "The required task is: " + task_input
        prompt += task_input
        
        steps = [
            "Identify and outline the sub-problems that need to be solved as stepping stones toward the solution. ",
            "Apply mathematical theorems, formulas to solve each sub-problem. ",
            "Integrate the solutions to these sub-problems in the previous step to get the final solution. "
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step

            start_time = time.time()
            # logger.info(f"{self.agent_name}")

            response = self.get_response(prompt)
            
            finished_time = time.time()
            # print(f"Finished time: {finished_time}")

            turnaround_time = finished_time - start_time
            turnaround_times.append(turnaround_time)
            
            prompt += response

        res = prompt
        self.set_status("Done")
        logger.info(f"{self.agent_name} has finished: Average turnaround time: {np.mean(np.array(turnaround_times))}\n")

        return res


    def parse_result(self, prompt):
        length = prompt.index("Response at step {} is: ")
        final_solution = prompt[length:]
        return final_solution


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MathAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = MathAgent(args.agent_name, args.task_input)

    agent_pool.append(agent)
    # agent_thread_pool.submit(agent.run)
    agent.run()
    # thread_pool.submit(agent.run)
    # agent.run()