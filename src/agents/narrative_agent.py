from src.agents.base import BaseAgent

import time

from src.agents.agent_process import (
    AgentProcess
)

from src.utils.global_param import (
    thread_pool,
    agent_process_queue
)

import argparse

from concurrent.futures import wait

class NarrativeAgent(BaseAgent):
    def __init__(self, agent_name, task_input):
        BaseAgent.__init__(self, agent_name, task_input)

    def run(self):
        
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
            agent_process = AgentProcess(self.get_aid(), self.get_agent_name(), prompt)
            self.send_request(agent_process)

            agent_process.set_status("Waiting")

            response = thread_pool.submit(self.get_response, agent_process)

            wait([response])

            agent_process.set_status("Done")
            prompt += "Generated content at step {} is: ".format(i) + agent_process.get_response()

        res = self.parse_result(prompt)
        # return res

        # time.sleep(10)
        self.set_status("Done")


    def parse_result(self, prompt):
        return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run NarrativeAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = NarrativeAgent(args.agent_name, args.task_input)

    agent.run()