
from .base_agent import BaseAgent

import time

from ..utils.chat_template import Query

import json

from aios.hooks.syscall import send_request

class ReactAgent(BaseAgent):
    def __init__(self,
                 agent_name,
                 task_input,
                #  agent_process_factory,
                 log_mode: str
        ):
        BaseAgent.__init__(
            self,
            agent_name,
            task_input,
            # agent_process_factory,
            log_mode
        )

        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

    def build_system_instruction(self):
        prefix = "".join(
            [
                "".join(self.config["description"])
            ]
        )

        plan_instruction = "".join(
            [
                f'You are given the available tools from the tool list: {json.dumps(self.tool_info)} to help you solve problems. ',
                'Generate a plan with comprehensive yet minimal steps to fulfill the task. ',
                'The plan must follow the json format as below: ',
                '[',
                '{"message": "message_value1","tool_use": [tool_name1, tool_name2,...]}',
                '{"message": "message_value2", "tool_use": [tool_name1, tool_name2,...]}',
                '...',
                ']',
                'In each step of the planned plan, identify tools to use and recognize no tool is necessary. ',
                'Followings are some plan examples. ',
                '['
                '[',
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "write a summarization based on the gathered information. ", "tool_use": []}',
                '];',
                '[',
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "understand the current methods and propose ideas that can improve ", "tool_use": []}',
                ']',
                ']'
            ]
        )

        if self.workflow_mode == "manual":
            self.messages.append(
                {"role": "system", "content": prefix}
            )

        else:
            assert self.workflow_mode == "automatic"
            self.messages.append(
                {"role": "system", "content": prefix}
            )
            self.messages.append(
                {"role": "user", "content": plan_instruction}
            )


    def automatic_workflow(self):
        return super().automatic_workflow()

    def manual_workflow(self):
        pass

    def run(self):
        super().run()
