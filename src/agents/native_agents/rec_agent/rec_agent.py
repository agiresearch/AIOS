from ...base import BaseAgent

import time

from ...agent_process import (
    AgentProcess
)

import argparse

from concurrent.futures import as_completed

import numpy as np
class RecAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 llm,
                 agent_process_queue,
                 agent_process_factory,
                 log_mode
        ):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue, agent_process_factory, log_mode)

    def run(self):
        prompt = ""
        prefix = self.prefix
        prompt += prefix
        task_input = self.task_input
        task_input = "The task you need to solve is: " + task_input
        self.logger.log(f"{task_input}\n", level="info")
        prompt += task_input
        waiting_times = []
        turnaround_times = []
        steps = [
            "give a general recommendation direction for users.",
            "based on the above recommendation direction, give a recommendation list."
        ]

        for i, step in enumerate(steps):
            prompt += f"\nIn step {i+1}, you need to {step}. Output should focus on current step and don't be verbose!"

            self.logger.log(f"Step {i+1}: {step}\n", level="info")

            response, waiting_time, turnaround_time = self.get_response(prompt)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)

            prompt += f"The solution to step {i+1} is: {response}\n"

            self.logger.log(f"The solution to step {i+1}: {response}\n", level="info")

        prompt += f"Given the interaction history: '{prompt}', give a final recommendation list and explanations, don't be verbose!"

        final_result, waiting_time, turnaround_time = self.get_response(prompt)
        # time.sleep(10)
        self.set_status("done")
        # print(f"Average waiting time: {np.mean(np.array(waiting_times))}")
        self.logger.log(
            f"Done. Average waiting time: {np.mean(np.array(waiting_times))} seconds. Average turnaround time: {np.mean(np.array(turnaround_times))} seconds\n",
            level="done"
        )

        self.logger.log(
            f"{task_input} Final result is: {final_result}\n",
            level="info"
        )

        return final_result

    def parse_result(self, prompt):
        return prompt

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run NarrativeAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = RecAgent(args.agent_name, args.task_input)
    agent.run()
