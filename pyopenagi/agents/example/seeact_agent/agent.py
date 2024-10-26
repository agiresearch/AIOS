import importlib
import os
import time
import json
from aios.hooks.request import send_request
from pyopenagi.utils.chat_template import Query
from pyopenagi.utils.logger import AgentLogger
from seeact.agent import SeeActAgent as SeeActCore

class SeeActAgent:
    def __init__(self, agent_name, task_input, log_mode: str):
        self.agent_name = agent_name
        self.config = self.load_config()
        self.tool_names = self.config.get("tools", [])
        
        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

        self.tool_list = dict()
        self.tools = []
        self.tool_info = []

        # 修改日志配置
        self.log_mode = log_mode
        self.logger = self.setup_logger()

        try:
            self.load_tools(self.tool_names)
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error loading tools: {str(e)}", "info")
            print(f"Error loading tools: {str(e)}")

        self.start_time = None
        self.end_time = None
        self.created_time = None
        self.request_waiting_times = []
        self.request_turnaround_times = []
        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"
        self.rounds = 0

        self.seeact = None
        self.set_status("active")
        self.set_created_time(time.time())

    def setup_logger(self):
        return AgentLogger(self.agent_name, self.log_mode)

    def load_tools(self, tool_names):
        if tool_names == "None":
            return

        for tool_name in tool_names:
            org, name = tool_name.split(".")[-2:]
            module_name = ".".join(["pyopenagi", "tools", org, name])
            class_name = self.snake_to_camel(name)

            tool_module = importlib.import_module(module_name)
            tool_class = getattr(tool_module, class_name)

            self.tool_list[name] = tool_class()
            tool_format = tool_class().get_tool_call_format()
            self.tools.append(tool_format)
            self.tool_info.append({
                "name": tool_format["function"]["name"],
                "description": tool_format["function"]["description"]
            })

    def run(self):
        self.build_system_instruction()
        task_input = self.task_input
        
        self.messages.append({"role": "user", "content": task_input})
        self.logger.log(f"{task_input}\n", level="info")
        
        workflow = self.manual_workflow()
        
        self.messages = self.messages[:1]
        
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

                    response, start_times, end_times, waiting_times, turnaround_times = send_request(
                        agent_name=self.agent_name,
                        query=Query(
                            messages=self.messages,
                            tools=selected_tools,
                            action_type=action_type
                        )
                    )

                    if self.rounds == 0:
                        self.set_start_time(start_times[0])

                    self.request_waiting_times.extend(waiting_times)
                    self.request_turnaround_times.extend(turnaround_times)

                    if i == len(workflow) - 1:
                        final_result = self.messages[-1]

                    step_result = self.messages[-1]["content"]
                    self.logger.log(f"At step {i + 1}, {step_result}\n", level="info")
                    self.rounds += 1

                self.set_status("done")
                self.set_end_time(time.time())

                return {
                    "agent_name": self.agent_name,
                    "result": final_result,
                    "rounds": self.rounds,
                    "agent_waiting_time": self.start_time - self.created_time if self.start_time else None,
                    "agent_turnaround_time": self.end_time - self.created_time if self.end_time else None,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times
                }
            else:
                return {
                    "agent_name": self.agent_name,
                    "result": "Failed to execute workflow",
                    "rounds": self.rounds,
                    "agent_waiting_time": None,
                    "agent_turnaround_time": None,
                    "request_waiting_times": self.request_waiting_times,
                    "request_turnaround_times": self.request_turnaround_times
                }
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error in run method: {str(e)}", "error")
            return {
                "status": "error",
                "error": str(e)
            }

    def manual_workflow(self):
        workflow = [
            {
                "action_type": "message_llm",
                "action": "Search for and navigate to the paper page",
                "tool_use": ["browser"],
            },
            {
                "action_type": "message_llm",
                "action": "Download the PDF file",
                "tool_use": ["downloader"],
            }
        ]
        return workflow

    def build_system_instruction(self):
        prefix = "".join(self.config["description"])
        self.messages.append({"role": "system", "content": prefix})

    def pre_select_tools(self, tool_names):
        pre_selected_tools = []
        for tool_name in tool_names:
            for tool in self.tools:
                if tool["function"]["name"] == tool_name:
                    pre_selected_tools.append(tool)
                    break
        return pre_selected_tools

    def load_config(self):
        script_path = os.path.abspath(__file__)
        script_dir = os.path.dirname(script_path)
        config_file = os.path.join(script_dir, "config.json")
        with open(config_file, "r") as f:
            return json.load(f)

    def snake_to_camel(self, snake_str):
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    def set_status(self, status):
        self.status = status

    def set_created_time(self, time):
        self.created_time = time

    def set_start_time(self, time):
        self.start_time = time

    def set_end_time(self, time):
        self.end_time = time