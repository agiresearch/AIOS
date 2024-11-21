import importlib

import os
import time

# from aios.hooks.syscall import send_request
from aios.hooks.syscall import useSysCall


from cerebrum.llm.communication import LLMQuery
from pyopenagi.utils.logger import AgentLogger

from pyopenagi.utils.utils import snake_to_camel

import json


class AcademicAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.tool_names = self.config["tools"]

        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

        self.send_request, _ = useSysCall()

        # self.agent_process_factory = agent_process_factory

        self.tool_list = dict()
        self.tools = []
        self.tool_info = (
            []
        )  # simplified information of the tool: {"name": "xxx", "description": "xxx"}

        self.load_tools(self.tool_names)

        self.start_time = None
        self.end_time = None
        self.request_waiting_times: list = []
        self.request_turnaround_times: list = []
        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"  # (mannual, automatic)
        self.rounds = 0

        self.log_mode = log_mode
        self.logger = self.setup_logger()


    def setup_logger(self):
        logger = AgentLogger(self.agent_name, self.log_mode)
        return logger

    def load_config(self):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        config_file = os.path.join(script_dir, "config.json")
        with open(config_file, "r") as f:
            config = json.load(f)
            return config
        
    def load_tools(self, tool_names):
        if tool_names == "None":
            return

        for tool_name in tool_names:
            org, name = tool_name.split("/")
            module_name = ".".join(["pyopenagi", "tools", org, name])
            class_name = snake_to_camel(name)

            tool_module = importlib.import_module(module_name)
            tool_class = getattr(tool_module, class_name)

            self.tool_list[name] = tool_class()
            tool_format = tool_class().get_tool_call_format()
            self.tools.append(tool_format)
            self.tool_info.append(
                {
                    "name": tool_format["function"]["name"],
                    "description": tool_format["function"]["description"],
                }
            )


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
                "tool_use": ["arxiv/arxiv"],
            },
            {
                "action_type": "chat",
                "action": "Provide responses based on the user's query",
                "tool_use": [],
            },
        ]
        return workflow
    
    def pre_select_tools(self, tool_names):
        pre_selected_tools = []
        for tool_name in tool_names:
            for tool in self.tools:
                if tool["function"]["name"] == tool_name:
                    pre_selected_tools.append(tool)
                    break

        return pre_selected_tools

    def run(self):
        self.build_system_instruction()

        task_input = self.task_input

        self.messages.append({"role": "user", "content": task_input})
        self.logger.log(f"{task_input}\n", level="info")

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
                    # "agent_waiting_time": None,
                    # "agent_turnaround_time": None,
                    # "request_waiting_times": self.request_waiting_times,
                    # "request_turnaround_times": self.request_turnaround_times,
                }
                
        except Exception as e:
            print(e)
            return {}
