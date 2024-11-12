from abc import ABC, abstractmethod
from typing import Callable, List

from pyopenagi.utils.chat_template import Response


class Action(ABC):

    def __init__(self, request_func: Callable[[List, List], Response]):
        self._request_func = request_func

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def format_prompt(self):
        pass
