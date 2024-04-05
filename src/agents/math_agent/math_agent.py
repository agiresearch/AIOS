# from src.agents.base import BaseAgent

from src.agents.base import BaseAgent

import os

import sys

from src.agents.agent_process import (
    AgentProcess
)

import argparse

from concurrent.futures import as_completed

import numpy as np

from src.agents.flow import Flow

from src.tools.online.currency_converter import CurrencyConverterAPI

from src.tools.online.wolfram_alpha import WolframAlpha
class MathAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 llm, agent_process_queue,
                 log_mode: str
        ):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue, log_mode)
        self.tool_list = {
            # "currency_converter": CurrencyConverterAPI,
            "wolfram_alpha": WolframAlpha,
            "currency_converter": CurrencyConverterAPI
        }
        self.tool_check_max_fail_times = 10
        self.tool_calling_max_fail_times = 10
        self.tool_info = "".join(self.config["tool_info"])
        self.load_flow()

    def load_flow(self):
        self.flow_ptr = Flow(self.config["flow"])

    def run(self):
        prompt = ""
        prefix = self.prefix
        task_input = self.task_input
        prompt += prefix
        waiting_times = []
        turnaround_times = []
        task_input = "The task you need to solve is: " + task_input
        self.logger.info(f"[{self.agent_name}] {task_input}\n")
        prompt += task_input

        # predefined steps
        steps = [
            "identify and outline the sub-problems that need to be solved as stepping stones toward the solution. ",
            "apply mathematical theorems, formulas to solve each sub-problem. ",
            "integrate the solutions to these sub-problems in the previous step to get the final solution. "
        ]
        for i, step in enumerate(steps):
            prompt += f"\nIn step {i+1}, you need to {step}. Output should focus on current step and don't be verbose!"
            self.logger.info(f"[{self.agent_name}] Step {i+1}: {step}\n")
            response, waiting_time, turnaround_time = self.get_response(prompt)
            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)
            prompt += f"The solution to step {i+1} is: {response}\n"
            self.logger.info(f"[{self.agent_name}] The solution to step {i+1}: {response}\n")

        # TODO test workflow of MathAgent
        # round_id = 1
        # flow_ptr = self.flow_ptr.header
        # logger.info(f'```\nFlows:\n{flow_ptr}```\n')
        # current_progress = []
        # questions, answers, output_record = [], [], []  # record each round: question, LLM output, tool output (if exists else LLM output)
        # while True:
        #     query = self.get_prompt(self.tool_info, flow_ptr, task_input, current_progress)
        #     prompt += query
        #     res, waiting_time,turnaround_time = self.get_response(query)

        #     prompt += res
        #     waiting_times.append(waiting_time)
        #     turnaround_times.append(turnaround_time)

        #     questions.append(str(flow_ptr))
        #     answers.append(res)

        #     prompt += res
        #     current_progress.append(f'Question {round_id}: ```{flow_ptr.get_instruction()}```')
        #     current_progress.append(f'Answer {round_id}: ```{res}```')

        #     # check tool use
        #     for k in range(self.tool_check_max_fail_times):
        #         tool_use, waiting_time, turnaround_time = self.check_tool_use(res, self.tool_info)
        #         waiting_times.append(waiting_time)
        #         turnaround_times.append(turnaround_time)
        #         if tool_use is not None:
        #             break

        #     if tool_use:
        #         tool, waiting_time, turnaround_time = self.check_tool_name(res, list(self.tool_list.keys()))
        #         waiting_times.append(waiting_time)
        #         turnaround_times.append(turnaround_time)

        #         tool, waiting_time, turnaround_time = self.tool_list[tool]
        #         waiting_times.append(waiting_time)
        #         turnaround_times.append(turnaround_time)

        #         for k in range(self.tool_calling_max_fail_times):
        #             try:
        #                 param = self.get_tool_arg(res, self.tool_info, tool)
        #                 param = [p.strip() for p in param.strip().split(',')]
        #                 tool_result = tool.run(*param)
        #                 output_record.append(tool_result)
        #                 current_progress.append(f'Observation {round_id}: ```{tool_result}```')
        #                 break
        #             except:
        #                 if k + 1 == self.tool_calling_max_fail_times:  # Max Fail attempts
        #                     logger.error('Reach Max fail attempts on Get Tool Parameters.')
        #                     break
        #                 else:
        #                     continue
        #     else:
        #         output_record.append(None)

        #     # terminate condition
        #     if len(flow_ptr.branch) == 0 and flow_ptr.type.lower() == 'terminal':
        #         break

        #     # check branch
        #     if len(flow_ptr.branch) == 1:  # no branches
        #         flow_ptr = list(flow_ptr.branch.values())[0]
        #     else:
        #         branch, waiting_time, turnaround_time = self.check_branch(res, flow_ptr)
        #         flow_ptr = flow_ptr.branch[branch]
        #     print(f'Current Block: \n```\n{flow_ptr}```')

        prompt += f"Given the interaction history: '{prompt}', integrate solutions in all steps to give a final answer, don't be verbose!"

        final_result, waiting_time, turnaround_time = self.get_response(prompt)
        waiting_times.append(waiting_time)
        turnaround_times.append(turnaround_time)

        self.set_status("Done")
        self.logger.info(f"[{self.agent_name}] has finished: average waiting time: {np.mean(np.array(waiting_times))} seconds, turnaround time: {np.mean(np.array(turnaround_times))} seconds\n")

        self.logger.info(f"[{self.agent_name}] {task_input} Final result is: {final_result}")

        return final_result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run MathAgent')
    parser.add_argument("--agent_name")
    parser.add_argument("--task_input")

    args = parser.parse_args()
    agent = MathAgent(args.agent_name, args.task_input)

    agent.run()
    # thread_pool.submit(agent.run)
    # agent.run()
