

import os
from cerebrum.agents.base import BaseAgent
from cerebrum.client import Cerebrum
from cerebrum.interface import AutoLLM, AutoTool

from cerebrum.llm.communication import LLMQuery

import json

class AcademicAgent(BaseAgent):
    def __init__(self, agent_name, task_input):
        super().__init__(agent_name, task_input)

        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

        self.start_time = None
        self.end_time = None
        self.request_waiting_times: list = []
        self.request_turnaround_times: list = []
        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"  # (mannual, automatic)
        self.rounds = 0


    def build_system_instruction(self):
        prefix = "".join(["".join(self.config["description"])])

        plan_instruction = "".join(
            [
                f"You are given the available tools from the tool list: {json.dumps(self.tool_info)} to help you solve problems. ",
                "Generate a plan with comprehensive yet minimal steps to fulfill the task. ",
                "The plan must follow the json format as below: ",
                "[",
                '{"message": "message_value1","tool_use": [tool_name1, tool_name2,...]}',
                '{"message": "message_value2", "tool_use": [tool_name1, tool_name2,...]}',
                "...",
                "]",
                "In each step of the planned plan, identify tools to use and recognize no tool is necessary. ",
                "Followings are some plan examples. ",
                "[" "[",
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "write a summarization based on the gathered information. ", "tool_use": []}',
                "];",
                "[",
                '{"message": "gather information from arxiv. ", "tool_use": ["arxiv"]},',
                '{"message", "understand the current methods and propose ideas that can improve ", "tool_use": []}',
                "]",
                "]",
            ]
        )

        if self.workflow_mode == "manual":
            self.messages.append({"role": "system", "content": prefix})

        else:
            assert self.workflow_mode == "automatic"
            self.messages.append({"role": "system", "content": prefix})
            self.messages.append({"role": "user", "content": plan_instruction})

    def automatic_workflow(self):
        for i in range(self.plan_max_fail_times):
            response = self.send_request(
                agent_name=self.agent_name,
                query=LLMQuery(
                    messages=self.messages, tools=None, message_return_type="json"
                ),
            )["response"]

            workflow = self.check_workflow(response.response_message)

            self.rounds += 1

            if workflow:
                return workflow

            else:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Fail {i+1} times to generate a valid plan. I need to regenerate a plan",
                    }
                )
        return None

    def manual_workflow(self):
        workflow = [
            {
                "action_type": "tool_use",
                "action": "Search for relevant papers",
                "tool_use": ["example/arxiv"],
            },
            {
                "action_type": "chat",
                "action": "Provide responses based on the user's query",
                "tool_use": [],
            },
        ]
        return workflow

    def run(self):
        self.build_system_instruction()

        task_input = self.task_input

        self.messages.append({"role": "user", "content": task_input})

        workflow = None

        if self.workflow_mode == "automatic":
            workflow = self.automatic_workflow()
            self.messages = self.messages[:1]  # clear long context

        else:
            assert self.workflow_mode == "manual"
            workflow = self.manual_workflow()

        self.messages.append(
            {
                "role": "user",
                "content": f"[Thinking]: The workflow generated for the problem is {json.dumps(workflow)}. Follow the workflow to solve the problem step by step. ",
            }
        )

        try:
            if workflow:
                final_result = ""

                for i, step in enumerate(workflow):
                    action_type = step["action_type"]
                    action = step["action"]
                    tool_use = step["tool_use"]

                    prompt = f"At step {i + 1}, you need to: {action}. "
                    self.messages.append({"role": "user", "content": prompt})

                    if tool_use:
                        selected_tools = self.pre_select_tools(tool_use)

                    else:
                        selected_tools = None

                    response = self.send_request(
                        agent_name=self.agent_name,
                        query=LLMQuery(
                            messages=self.messages,
                            tools=selected_tools,
                            action_type=action_type,
                        ),
                    )["response"]
                    
                    self.messages.append({"role": "assistant", "content": response.response_message})

                    self.rounds += 1

                # print(final_result)
                final_result = self.messages[-1]["content"]
                
                print(final_result)
                return {
                    "agent_name": self.agent_name,
                    "result": final_result,
                    "rounds": self.rounds,
                }

            else:
                return {
                    "agent_name": self.agent_name,
                    "result": "Failed to generate a valid workflow in the given times.",
                    "rounds": self.rounds,

                }
                
        except Exception as e:

            return {}
