from abc import ABC, abstractmethod


class Action(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @abstractmethod
    def format_prompt(self):
        pass

    @staticmethod
    def display():
        pass
