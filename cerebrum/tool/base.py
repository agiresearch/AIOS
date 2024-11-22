class BaseTool:
    """Base class for calling tools
    """
    def __init__(self) -> None:
        pass

    def run(self, params) -> None:
        pass

    def get_tool_call_format(self) -> dict:
        """Get tool calling format following the function calling from OpenAI: https://platform.openai.com/docs/guides/function-calling
        """
        pass

class BaseRapidAPITool(BaseTool):
    """Base class for calling tools from rapidapi hub: https://rapidapi.com/hub
    """
    def __init__(self):
        super().__init__()
        self.url: str = None
        self.host_name: str = None
        self.api_key: str = None

    def run(self, params: dict):
        pass

    def get_tool_call_format(self) -> dict:
        pass


class BaseHuggingfaceTool(BaseTool):
    """Base class for calling models from huggingface

    """
    def __init__(self):
        super().__init__()
        self.url: str = None
        self.host_name: str = None
        self.api_key: str = None

    def run(self, params: dict):
        pass

    def get_tool_call_format(self) -> dict:
        pass
