from src.utils.utils import get_from_env
import json
class BaseTool:
    """Base class for calling tool
    """
    def __init__(self):
        pass

    def run(self):
        pass
class BaseRapidAPITool(BaseTool):
    """Base class for calling tool from Rapid api hub

    Args:
        BaseTool (_type_): _description_
    """
    def __init__(self):
        super().__init__()
        self.search_url: str = None
        self.host_name: str = None
        self.urban_dict_api_key = None


    def run(self, prompt):
        pass

    def parse_result(self, response: json):
        pass
