from src.agents.base import BaseAgent

import time

from src.agents.agent_process import (
    AgentProcess
)

# from src.utils.global_param import (
#     agent_thread_pool,
#     agent_process_queue,
#     llm
# )
from src.utils.utils import (
    logger
)

import numpy as np

import argparse

from concurrent.futures import as_completed

class NarrativeAgent(BaseAgent):
    def __init__(self, agent_name, task_input, llm, agent_process_queue):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue)

    def run(self):
        waiting_times = []
        turnaround_times = []
        prompt = ""
        prefix = self.prefix
        prompt += prefix
        task_input = self.task_input
        task_input = "Given the task: " + task_input
        prompt += task_input
        
        steps = [
            "Develop the story's setting and characters, establish a background and introduce the main characters.",
            "Given the background and characters, create situations that lead to the rising action, develop the climax with a significant turning point, and then move towards the resolution.",
            "Conclude the story and reflect on the narrative. This could involve tying up loose ends, resolving any conflicts, and providing a satisfactory conclusion for the characters."
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step
            
            start_time = time.time()
            response = self.get_response(prompt)

            finished_time = time.time()

            turnaround_time = finished_time - start_time
            turnaround_times.append(turnaround_time)

            prompt += response

        # res = self.parse_result(prompt)
        res = prompt
        # return res
        # print(f"Average waiting time: {np.mean(np.array(waiting_times))}")
        logger.info(f"{self.agent_name} has finished: Average turnaround time: {np.mean(np.array(turnaround_times))}\n")

        # time.sleep(10)
        self.set_status("Done")

        return res

    def parse_result(self, prompt):
        return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run NarrativeAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = NarrativeAgent(args.agent_name, args.task_input)

    agent.run()
    # agent_thread_pool.submit(agent.run)
    # agent.run()