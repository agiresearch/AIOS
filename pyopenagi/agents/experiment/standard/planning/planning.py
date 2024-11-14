import re
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
        if tool_calls := response.tool_calls:
            response_message = None
        else:
            response_message = response.response_message

        result = PlanningResult()
        result.text_content = response_message

        if tool_calls:
            # action tool
            result.action_type = "TOOL"
            result.action_param = {
                "tool_call": tool_calls[0]
            }
            return result

        if code_info := extract_code(response_message):
            # action code
            result.action_type = "CODE"
            result.action_param = {
                "code": code_info[0],
                "requirements": code_info[1],
            }
            return result

        return result

    def format_prompt(self):
        return {
            "name": "normal",
            "description": "Try to solve promble step by step. Think more before you try to give final answer."
        }


def extract_code(message) -> tuple[str, str] | None:
    """extract code from message"""
    code_match = re.search(r'```python\s*([\s\S]*?)```', message)
    requirements_match = re.search(r'```requirements\s*([\s\S]*?)```', message)

    code = code_match.group(1) if code_match else None
    requirements = requirements_match.group(1) if requirements_match else None
    return code, requirements
