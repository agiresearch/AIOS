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

import re
class MathAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                 llm, agent_process_queue,
                 log_mode: str
        ):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue, log_mode)
        self.tool_list = {
            "wolfram_alpha": WolframAlpha(),
        }
        self.tool_check_max_fail_times = 10
        self.tool_select_max_fail_times = 10
        self.tool_calling_max_fail_times = 10
        self.tool_info = "".join(self.config["tool_info"])
        self.load_flow()

    def load_flow(self):
        self.flow_ptr = Flow(self.config["flow"])

    def check_tool_use(self, prompt, tool_info, temperature=0.):
        self.logger.info(prompt)
        prompt = f'You are allowed to use the following tools: {tool_info}' \
                f'Based on current progress: "{prompt}", do you think the current progress calls any tool?\n' \
                f'Only answer "Yes" or "No".'
        response, waiting_time, turnaround_time = self.get_response(prompt, temperature)
        if 'yes' in response.lower():
            return True, waiting_time, turnaround_time
        if 'no' in response.lower():
            return False, waiting_time, turnaround_time
        return None, waiting_time, turnaround_time

    def get_prompt(self, tool_info, flow_ptr, task_description, cur_progress):
        progress_str = '\n'.join(cur_progress)
        prompt = f'Available tools: {tool_info}; Current Progress: {progress_str}; Task description: {task_description}; ' \
                f'Question: {flow_ptr.get_instruction()}; Only answer the current instruction and do not be verbose.'
        return prompt

    def get_tool_arg(self, prompt, tool_info, selected_tool, temperature=0.0):
        prompt = f'You attempt to use the tool {selected_tool}. ' \
                f'Based on current progress: {prompt} and the tool information: {tool_info}, what is the argument you need to pass to call tool for this step? ' \
                f'Respond "None" if no arguments are needed for this tool. Only output the param without any other information. '\
                f'Separate by comma if there are multiple arguments. Do not be verbose!'
        response, waiting_time, turnaround_time = self.get_response(prompt)
        if  re.search(r'none', response, re.IGNORECASE):
            return None, waiting_time, turnaround_time
        return response, waiting_time, turnaround_time

    def check_tool_name(self, prompt, tool_list, temperature=0.):
        prompt = f'Based on current progress: {prompt}, choose the number (ranging from 1 to {len(tool_list)}) of the tool you will use from the following tool list: ['
        for i, key in enumerate(tool_list):
            prompt += f'{i + 1}: {key}.'
        prompt += f"]. Your answer should be only an number. Don't be verbose! "
        response, waiting_time, turnaround_time = self.get_response(prompt, temperature=temperature)
        if response.isdigit() and 1 <= int(response) <= len(tool_list):
            response = int(response)
            return tool_list[response - 1], waiting_time, turnaround_time
        else:
            return None, waiting_time, turnaround_time

    def check_branch(self, prompt, flow_ptr, temperature=0.):
        possible_keys = list(flow_ptr.branch.keys())
        # self.logger.info(possible_keys)

        prompt = f'Based on the current progress: "{prompt}", choose the closest branch representation from the following branch list: ['
        for i, key in enumerate(possible_keys):
            prompt += f'{i + 1}: {key}.'
        prompt += "]. Your answer should be only an number, referring to the desired choice. Don't be verbose!"
        response, waiting_time, turnaround_time = self.get_response(prompt=prompt, temperature=temperature)
        if response.isdigit() and 1 <= int(response) <= len(possible_keys):
            response = int(response)
            return possible_keys[response - 1], waiting_time, turnaround_time
        else:
            return None, waiting_time, turnaround_time

    def run(self):
        prompt = ""
        prefix = self.prefix
        task_input = self.task_input
        prompt += prefix
        waiting_times = []
        turnaround_times = []
        task_input = "The task you need to solve is: " + task_input
        self.logger.info(f"[{self.agent_name}] {task_input}\n")

        # TODO test workflow of MathAgent
        round_id = 1
        flow_ptr = self.flow_ptr.header
        current_progress = []
        questions, answers, output_record = [], [], []  # record each round: question, LLM output, tool output (if exists else LLM output)
        while True:
            query = self.get_prompt(self.tool_info, flow_ptr, task_input, current_progress)
            res, waiting_time,turnaround_time = self.get_response(query)

            waiting_times.append(waiting_time)
            turnaround_times.append(turnaround_time)

            questions.append(str(flow_ptr))
            answers.append(res)

            current_progress.append(f'Question {round_id}: {flow_ptr.get_instruction()}')
            current_progress.append(f'Answer {round_id}: {res}')

            self.logger.info(
                f"[{self.agent_name}] In round {round_id}, the {self.agent_name} proposes the question '{current_progress[-2]}'" \
                f"and get the answer '{current_progress[-1]}'. "
            )

            # check tool use
            for k in range(self.tool_check_max_fail_times):
                tool_use, waiting_time, turnaround_time = self.check_tool_use(
                    " ".join(current_progress[-2:]),
                    self.tool_info,
                    temperature = 0.1 * (k+1)
                )
                # self.logger.info(f"Tool use: {tool_use}")
                waiting_times.append(waiting_time)
                turnaround_times.append(turnaround_time)
                if tool_use is not None:
                    break

            if tool_use:
                for k in range(self.tool_select_max_fail_times):
                    tool_name, waiting_time, turnaround_time = self.check_tool_name(
                        " ".join(current_progress[-2:]),
                        list(self.tool_list.keys()),
                        temperature = 0.1 * (k+1)
                    )
                    if tool_name is not None:
                        break

                self.logger.info(f"[{self.agent_name}] has decided to call tool: {tool_name}. ")
                waiting_times.append(waiting_time)
                turnaround_times.append(turnaround_time)

                tool = self.tool_list[tool_name]

                for k in range(self.tool_calling_max_fail_times):
                    param, waiting_time, turnaround_time = self.get_tool_arg(
                        " ".join(current_progress[-2:]),
                        self.tool_info,
                        tool,
                        temperature = 0.1 * (k+1)
                    )

                    if param is None:
                        if k + 1 == self.tool_calling_max_fail_times:  # Max Fail attempts
                            self.logger.info(f'[{self.agent_name}] It has reached maximum fail attempts on get tool parameters. ')
                            break
                        else:
                            continue
                    else:
                        self.logger.info(f"[{self.agent_name}] It has chose the param {param} to use the tool: {tool_name}. ")
                        # param = [p.strip() for p in param.strip().split(',')]
                        tool_result = tool.run(param)

                        self.logger.info(f"[{self.agent_name}] The result of executing tool {tool_name} is: {tool_result}. ")

                        output_record.append(tool_result)
                        current_progress.append(f'Observation {round_id}: {tool_result}')
                        break
            else:
                output_record.append(None)

            # terminate condition
            if len(flow_ptr.branch) == 0 and flow_ptr.type.lower() == 'terminal':
                break

            # check branch
            if len(flow_ptr.branch) == 1:  # no branches
                flow_ptr = list(flow_ptr.branch.values())[0]
            else:
                branch, waiting_time, turnaround_time = self.check_branch(current_progress[:-2], flow_ptr)
                flow_ptr = flow_ptr.branch[branch]
            round_id += 1

        prompt = self.get_prompt(self.tool_info, flow_ptr, task_input, current_progress)

        prompt += f"Given the interaction history: '{prompt}', integrate solutions in all steps to give a final answer, don't be verbose!"

        final_result, waiting_time, turnaround_time = self.get_response(prompt)
        waiting_times.append(waiting_time)
        turnaround_times.append(turnaround_time)

        self.set_status("done")
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
