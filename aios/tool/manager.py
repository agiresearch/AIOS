import importlib

from cerebrum.llm.communication import Response
from cerebrum.interface import AutoTool

class ToolManager:
    def __init__(
        self,
        log_mode: str = "console",
    ):
        self.log_mode = log_mode
        self.tool_conflict_map = {}

    def address_request(self, syscall) -> None:
        
        tool_calls = syscall.tool_calls

        try:
            for tool_call in tool_calls:
                tool_org_and_name, tool_params = (
                    tool_call["name"],
                    tool_call["parameters"],
                )
                # org, tool_name = tool_org_and_name.split("/")

                if tool_org_and_name not in self.tool_conflict_map.keys():
                    self.tool_conflict_map[tool_org_and_name] = 1
                    tool = self.load_tool_instance(tool_org_and_name)

                    # tool = tool_class()
                    tool_result = tool.run(params=tool_params)

                    self.tool_conflict_map.pop(tool_org_and_name)
                    
                    return Response(
                        response_message=tool_result,
                        finished=True
                    )
                    
        except Exception as e:
            return Response(
                response_message=f"Tool calling error: {e}",
                finished=True
            )

    def load_tool_instance(self, tool_org_and_name):

        tool_instance = AutoTool.from_preloaded(tool_org_and_name)
        return tool_instance
