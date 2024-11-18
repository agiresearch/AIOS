import os
import json
import time

from cerebrum.utils.chat import Query
from cerebrum.runtime.process import AgentProcessor
import importlib

class BaseAgent:
    def __init__(self, 
                 agent_name: str, 
                 task_input: str, 
                 config: dict):
        # super().__init__()
        self.agent_name = agent_name
        self.config = config

        self.tool_list = dict()
        self.tools = []
        self.tool_info = ([])  # simplified information of the tool: {"name": "xxx", "description": "xxx"}

        self.load_tools(self.config.get('tools'))
        self.rounds = 0

        self.task_input = task_input
        self.messages = []
        self.workflow_mode = "manual"  # (manual, automatic)

        self.llm = None


    def run(self):
        # raise NotImplementedError
        pass

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
            response = AgentProcessor.process_response(query=Query(messages=self.messages, tools=None, message_return_type="json"), llm=self.llm)
            
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
        if tool_names == None:
            return

        for tool_name in tool_names:
            org, name = tool_name.split("/")
            module_name = ".".join(["cerebrum", "tools", org, name])
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

    def create_agent_request(self, query):
        agent_process = self.agent_process_factory.activate_agent_process(
            agent_name=self.agent_name, query=query
        )
        agent_process.set_created_time(time.time())
        # print("Already put into the queue")
        return agent_process

    def set_aid(self, aid):
        self.aid = aid

    def get_aid(self):
        return self.aid

    def get_agent_name(self):
        return self.agent_name


