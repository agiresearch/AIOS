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
            # agent_process = AgentProcess(self.get_aid(), self.get_agent_name(), prompt)
            # self.send_request(agent_process)

            # agent_process.set_status("Waiting")

            # response = agent_process_queue.submit(self.get_response, agent_process)
            print("Narrative Agent")

            start_time = time.time()
            print(f"Start time: {start_time}")
            args = [prompt, start_time]
            task = self.agent_process_queue.submit(lambda p:self.get_response(*p), args)

            response = ""
            waiting_time = -1
            for r in as_completed([task]):
                response, waiting_time = r.result()
            waiting_times.append(waiting_time)
            finished_time = time.time()
            print(f"Finished time: {finished_time}")

            turnaround_time = finished_time - start_time
            turnaround_times.append(turnaround_time)

            # print(f"Turnaround time: {turnaround_time}\n")

            # print(response)
            # print(agent_process.get_response())

            # agent_process.set_status("Done")
            # prompt += "Generated content at step {} is: ".format(i) + agent_process.get_response()
            prompt += "Generated content at step {} is: ".format(i) + response

        res = self.parse_result(prompt)
        # return res
        print("Narrative Agent")
        print(f"Avg waiting time: {np.mean(np.array(waiting_times))}")
        print(f"Avg turnaround time: {np.mean(np.array(turnaround_times))}\n")

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
    # agent_thread_pool.submit(agent.run)
    # agent.run()