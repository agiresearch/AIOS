import importlib
from typing import Any

from pyopenagi.agents.experiment.standard.action.action import Action
from pyopenagi.agents.experiment.standard.utils.config import Config
from pyopenagi.agents.experiment.standard.utils.str_utils import snake_to_camel


class ActionTool(Action):

    def __init__(self, config: Config):
        super().__init__()
        self.tools = {}
        self.tools_format = []
        self.type = "TOOL"
        self.config = config
        self.init_tools()

    def __call__(self, tool_call: dict) -> Any:
        if tool_call is None:
            return

        function_name = tool_call["name"]
        function_param = tool_call["parameters"]
        try:
            function_call = self.tools[function_name]
            function_response = function_call.run(function_param)

        except TypeError:
            function_response = f"Call function {function_name} failed. Parameters {function_param} is invalid."

        return function_response, tool_call["id"]

    def init_tools(self):
        self._init_tools_from_config()

    def _init_tools_from_config(self):
        tool_names = self.config.tools
        if tool_names == "None":
            return

        for tool_name in tool_names:
            org, name = tool_name.split("/")
            module_name = ".".join(["pyopenagi", "tools", org, name])
            class_name = snake_to_camel(name)

            tool_module = importlib.import_module(module_name)
            tool_class = getattr(tool_module, class_name)

            self.tools[name] = tool_class()
            tool_format = tool_class().get_tool_call_format()
            self.tools_format.append(tool_format)

    def format_prompt(self):
        return {
            "name": "tool use",
            "description": ""
        }

    @staticmethod
    def display():
        return False
