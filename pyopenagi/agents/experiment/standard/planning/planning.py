from abc import ABC, abstractmethod
from typing import List, Callable

from pyopenagi.utils.chat_template import Response


class Planning(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass


class DefaultPlanning(Planning):

    def __call__(self, messages: List, tools: List, request_func: Callable[[List, List], Response]):
        return
