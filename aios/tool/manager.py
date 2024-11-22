import importlib

from cerebrum.llm.communication import Response

class ToolManager:
    def __init__(
        self,
        log_mode: str = "console",
    ):
        self.log_mode = log_mode
        self.tool_conflict_map = {}

    def address_request(self, syscall) -> None:
        tool_calls = syscall.tool_calls
        for tool_call in tool_calls:
            tool_org_and_name, tool_params = (
                tool_call["name"],
                tool_call["parameters"],
            )
            # org, tool_name = tool_org_and_name.split("/")

            if tool_org_and_name not in self.tool_conflict_map.keys():
                self.tool_conflict_map[tool_org_and_name] = 1
                tool_class = self.load_tool_instance(tool_org_and_name)

                tool = tool_class()
                tool_result = tool.run(params=tool_params)

                self.tool_conflict_map.pop(tool_org_and_name)
                
                return Response(
                    response_message=tool_result,
                    finished=True
                )

    def load_tool_instance(self, tool_org_and_name):
        def snake_to_camel(s):
            pass
        
        org, tool_name = tool_org_and_name.split("/")
        module_name = ".".join(["pyopenagi", "tools", org, tool_name])
        class_name = snake_to_camel(tool_name)
        tool_module = importlib.import_module(module_name)
        tool_instance = getattr(tool_module, class_name)
        return tool_instance
