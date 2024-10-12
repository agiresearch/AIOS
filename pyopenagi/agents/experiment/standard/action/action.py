from abc import ABC, abstractmethod


class Action(ABC):

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass
