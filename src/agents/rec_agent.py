from src.agents.base import BaseAgent

import time

from src.agents.agent_process import (
    AgentProcess
)

# from src.utils.global_param import (
#     agent_thread_pool,
#     agent_process_queue,
# )

import argparse

from concurrent.futures import as_completed

import numpy as np

class RecAgent(BaseAgent):
    def __init__(self, agent_name, task_input, llm, agent_process_queue):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue)

    def run(self):
        
        prompt = ""
        prefix = self.prefix
        prompt += prefix
        task_input = self.task_input
        task_input = "Given the task: " + task_input
        prompt += task_input
        waiting_times = []
        turnaround_times = []
        steps = [
            "Give a general recommendation direction for users.",
            "Based on the above recommendation direction, give a recommendation list."
        ]

        for i, step in enumerate(steps):
            prompt += "In step {}: ".format(i) + step
            print("Rec Agent")

            start_time = time.time()

            # print(f"Start time: {start_time}")

            args = [prompt, start_time]
            task = self.agent_process_queue.submit(lambda p:self.get_response(*p), args)

            response = ""
            waiting_time = -1
            for r in as_completed([task]):
                response, waiting_time = r.result()
            waiting_times.append(waiting_time)
            finished_time = time.time()
            # print(f"Finished time: {finished_time}")

            turnaround_time = finished_time - start_time
            turnaround_times.append(turnaround_time)
            # print(f"Turnaround time: {turnaround_time}")

            # print(response)
            # print(agent_process.get_response())

            # agent_process.set_status("Done")
            # prompt += "Generated content at step {} is: ".format(i) + agent_process.get_response()
            prompt += "Generated content at step {} is: ".format(i) + response

        # res = self.parse_result(prompt)
        res = prompt

        # time.sleep(10)
        self.set_status("Done")
        print("Rec Agent")
        print(f"Average waiting time: {np.mean(np.array(waiting_times))}")
        print(f"Average turnaround time: {np.mean(np.array(turnaround_times))}\n")

        return res

    def parse_result(self, prompt):
        return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run NarrativeAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = RecAgent(args.agent_name, args.task_input)
    # agent_thread_pool.submit(agent.run)
    agent.run()