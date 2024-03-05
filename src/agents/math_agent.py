# from src.agents.base import BaseAgent

from src.agents.base import BaseAgent

import os

import time

import sys

from src.agents.agent_process import (
    AgentProcess
)

from src.utils.global_param import (
    thread_pool,
    agent_process_queue,
    agent_pool
)

import argparse

from concurrent.futures import wait

class MathAgent(BaseAgent):
    def __init__(self, agent_name, task_input):
        BaseAgent.__init__(self, agent_name, task_input)
        print(agent_name + " has been initialized.")
        
    
    def run(self):
        prompt = ""
        prefix = self.prefix
        task_input = self.task_input
        prompt += prefix
        
        task_input = "The required task is: " + task_input
        prompt += task_input
        
        steps = [
            "Identify and outline the sub-problems that need to be solved as stepping stones toward the solution.",
            "Apply mathematical theorems, formulas to solve each sub-problem.",
            "Integrate the solutions to these sub-problems in the previous step to get the final solution."
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step

            # FIFO request and response
            time.sleep(5)
            
            agent_process = AgentProcess(self.get_aid(), self.get_agent_name(), prompt)
            self.send_request(agent_process)

            print("Request has been sent.")

            agent_process.set_status("Waiting")

            response = thread_pool.submit(self.get_response, agent_process)

            wait([response])

            agent_process.set_status("Done")
            
            prompt += "Response at step {} is: ".format(i) + agent_process.get_response()

        res = self.parse_result(prompt)
        time.sleep(10)
        self.set_status("Done")

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

    thread_pool.submit(agent.run)
    # agent.run()