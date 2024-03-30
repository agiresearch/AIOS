from src.agents.base import BaseAgent

import os

import time

import sys

from src.agents.agent_process import (
    AgentProcess
)

from concurrent.futures import as_completed

import numpy as np

from src.tools.online.bing_search import BingSearch

from src.tools.online.google_search import GoogleSearch

from src.tools.online.arxiv import Arxiv

from src.agents.flow import Flow

class TravelAgent(BaseAgent):
    def __init__(self, agent_name, task_input, llm, agent_process_queue):
        BaseAgent.__init__(self, agent_name, task_input, llm, agent_process_queue)
        
        self.tool_list = {
            "google_search": GoogleSearch(),
            # "bing_search": BingSearch(),
            # "arxiv": Arxiv()
        }

        self.tool_calling_max_fail_times = 10

        self.tool_info = "".join(self.config["tool_info"])

        self.prefix = "".join(self.config["description"])

        self.load_flow()

    def load_flow(self):
        self.flow_ptr = Flow(self.config["flow"])

    def run(self):
        # all_plans = []
        query = self.prefix + "The task is: " + self.task_input
        plan_round = 1
        flow_ptr = self.flow_ptr.header
        # for idx, query in enumerate(tqdm(query_data_list)):
        # idx, query = 0, query_data_list[0]['query']
        # flow_ptr = flow.header
        # logging.info(f'```\nFlows:\n{flow}```\n')
        current_progress = []
        questions, answers, output_record = [], [], []  # record each round: question, LLM output, tool output (if exists else LLM output)
        while True:
            prompt = self.get_prompt(self.tool_info, flow_ptr, query, current_progress)
            res = self.get_response(prompt)
            
            questions.append(str(flow_ptr))
            answers.append(str(res))
            current_progress.append(f'Question {plan_round}: ```{flow_ptr.get_instruction()}```')
            current_progress.append(f'Answer {plan_round}: ```{res}```')

            # check tool use
            tool_use = self.check_tool_use(res, self.tool_info)
            if tool_use:
                tool = self.check_tool_name(res, list(self.tool_list.keys()))
                tool = self.tool_list[tool]
                for k in range(self.tool_calling_max_fail_times):
                    try:
                        param = self.get_tool_arg(res, self.tool_info, tool)
                        param = [p.strip() for p in param.strip().split(',')]
                        tool_result = tool.run(*param)
                        output_record.append(tool_result)
                        current_progress.append(f'Observation {plan_round}: ```{tool_result}```')
                        break
                    except:
                        if k + 1 == self.tool_calling_max_fail_times:  # Max Fail attempts
                            print('Reach Max fail attempts on Get Tool Parameters.')
                            exit(1)
                        else:
                            continue
            else:
                output_record.append(None)

            # terminate condition
            if len(flow_ptr.branch) == 0 and flow_ptr.type.lower() == 'terminal':
                break

            # check branch
            if len(flow_ptr.branch) == 1:  # no branches
                flow_ptr = list(flow_ptr.branch.values())[0]
            else:
                branch = self.check_branch(res, flow_ptr)
                flow_ptr = flow_ptr.branch[branch]
            print(f'Current Block: \n```\n{flow_ptr}```')

            plan_round += 1
