from abc import ABC, abstractmethod


class Communication(ABC):

    @abstractmethod
    def send(self, *args, **kwargs):
        pass

    @abstractmethod
    def receive(self, *args, **kwargs):
        pass
