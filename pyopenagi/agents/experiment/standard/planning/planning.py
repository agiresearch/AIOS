from abc import ABC, abstractmethod
from typing import List, Callable, Optional, Any

from pydantic.v1 import BaseModel

from pyopenagi.utils.chat_template import Response


class PlanningResult(BaseModel):
    text_content: Optional[str]
    action_type: Optional[str]
    action_param: Optional[Any]


class Planning(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def format_prompt(self):
        pass


class DefaultPlanning(Planning):

    def __init__(self, request_func: Callable[[List, List], Response]):
        self.request_func = request_func

    def __call__(self, messages: List, tools: List):
        response = self.request_func(messages, tools)
        response_message = response.response_message
        tool_calls = response.tool_calls

        result = PlanningResult()
        result.text_content = response_message
        if tool_calls:
            result.action_type = "TOOL"
            result.action_param = {
                "tool_call": tool_calls[0]
            }

        return result

    def format_prompt(self):
        return {
            "name": "normal",
            "description": "Planning as normal."
        }
