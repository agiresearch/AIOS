# from src.agents.base import BaseAgent

from src.agents.base import BaseAgent

import os

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
        task_input = "The task you need to solve is: " + task_input
        logger.info(f"[{self.agent_name}] {task_input}\n")
        prompt += task_input
        
        steps = [
            "identify and outline the sub-problems that need to be solved as stepping stones toward the solution. ",
            "apply mathematical theorems, formulas to solve each sub-problem. ",
            "integrate the solutions to these sub-problems in the previous step to get the final solution. "
        ]

        for i, step in enumerate(steps):
            prompt += f"\nIn step {i+1}, you need to {step}. Output should focus on current step and don't be verbose!"

            logger.info(f"[{self.agent_name}] Step {i+1}: {step}\n")

            response, waiting_time, turnaround_time = self.get_response(prompt)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)

            prompt += f"The solution to step {i+1} is: {response}\n"

            logger.info(f"[{self.agent_name}] The solution to step {i+1}: {response}\n")

        prompt += f"Given the interaction history: '{prompt}', integrate solutions in all steps to give a final answer, don't be verbose!"

        final_result, waiting_time, turnaround_time = self.get_response(prompt)
        waiting_times.append(waiting_time)
        turnaround_times.append(turnaround_time)

        self.set_status("Done")
        logger.info(f"{self.agent_name} has finished: average waiting time: {np.mean(np.array(waiting_times))} seconds, turnaround time: {np.mean(np.array(turnaround_times))} seconds\n")

        logger.info(f"[{self.agent_name}] {task_input} Final result is: {final_result}")

        return final_result


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