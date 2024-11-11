import importlib

class ToolManager:
    def __init__(
        self,
        log_mode: str = "console",
    ):
        self.log_mode = log_mode
        self.tool_conflict_map = {}

    def tool_run(self, syscall, temperature=0.0) -> None:
        request_data = syscall.request_data
        tool_org_and_name, tool_params = request_data["name"], request_data["paramemters"]
        org, tool_name = tool_org_and_name.split("/")
        
        if tool_name not in self.tool_conflict_map.keys():
            self.tool_conflict_map[tool_name] = 1
            tool_class = self.load_tool_instance(tool_name)

            tool = tool_class(
                tool_name=tool_name
            )
            tool.run(
                params = tool_params
            )
            
            self.tool_conflict_map.pop(tool_name)

    def snake_to_camel(self, snake_str):
        components = snake_str.split("_")
        return "".join(x.title() for x in components)

    def load_tool_instance(self, tool_org_and_name):
        org, tool_name = tool_org_and_name.split("/")
        module_name = ".".join(["pyopenagi", "tools", org, tool_name])
        class_name = self.snake_to_camel(tool_name)
        tool_module = importlib.import_module(module_name)
        tool_instance = getattr(tool_module, class_name)
        return tool_instance
