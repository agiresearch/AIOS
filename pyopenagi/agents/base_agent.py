import os

import json

import time

from threading import Thread

import threading

from ..utils.logger import AgentLogger

from ..utils.chat_template import Query

import importlib

from aios.hooks.syscall import send_request

class BaseAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        # super().__init__()
        self.agent_name = agent_name
        self.config = self.load_config()
        self.tool_names = self.config["tools"]
        
        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

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

        self.set_status("active")
        self.set_created_time(time.time())

    def run(self):
        """Execute each step to finish the task."""
        # self.set_aid(threading.get_ident())
        self.logger.log(
            f"{self.agent_name} starts running. Agent ID is {self.get_aid()}\n",
            level="info",
        )

    # can be customization
    def build_system_instruction(self):
        pass

    def check_workflow(self, message):
        try:
            # print(f"Workflow message: {message}")
            workflow = json.loads(message)
            if not isinstance(workflow, list):
                return None

            for step in workflow:
                if "message" not in step or "tool_use" not in step:
                    return None

            return workflow

        except json.JSONDecodeError:
            return None

    def automatic_workflow(self):
        for i in range(self.plan_max_fail_times):
            response, start_times, end_times, waiting_times, turnaround_times = send_request(
                agent_name = self.agent_name,
                query=Query(
                    messages=self.messages, tools=None, message_return_type="json"
                )
            )

            if self.rounds == 0:
                self.set_start_time(start_times[0])

            self.request_waiting_times.extend(waiting_times)
            self.request_turnaround_times.extend(turnaround_times)

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
        pass

    def check_path(self, tool_calls):
        script_path = os.path.abspath(__file__)
        save_dir = os.path.join(
            os.path.dirname(script_path), "output"
        )  # modify the customized output path for saving outputs
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        for tool_call in tool_calls:
            try:
                for k in tool_call["parameters"]:
                    if "path" in k:
                        path = tool_call["parameters"][k]
                        if not path.startswith(save_dir):
                            tool_call["parameters"][k] = os.path.join(
                                save_dir, os.path.basename(path)
                            )
            except Exception:
                continue
        return tool_calls

    def snake_to_camel(self, snake_str):
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    def load_tools(self, tool_names):
        if tool_names == "None":
            return

        for tool_name in tool_names:
            org, name = tool_name.split("/")
            module_name = ".".join(["pyopenagi", "tools", org, name])
            class_name = self.snake_to_camel(name)

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

    def pre_select_tools(self, tool_names):
        pre_selected_tools = []
        for tool_name in tool_names:
            for tool in self.tools:
                if tool["function"]["name"] == tool_name:
                    pre_selected_tools.append(tool)
                    break

        return pre_selected_tools

    def setup_logger(self):
        logger = AgentLogger(self.agent_name, self.log_mode)
        return logger

    def load_config(self):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        config_file = os.path.join(script_dir, self.agent_name, "config.json")
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name

    def set_status(self, status):
        """
        Status type: Waiting, Running, Done, Inactive
        """
        self.status = status

    def get_status(self):
        return self.status

    def set_created_time(self, time):
        self.created_time = time

    def get_created_time(self):
        return self.created_time

    def set_start_time(self, time):
        self.start_time = time

    def get_start_time(self):
        return self.start_time

    def set_end_time(self, time):
        self.end_time = time

    def get_end_time(self):
        return self.end_time
