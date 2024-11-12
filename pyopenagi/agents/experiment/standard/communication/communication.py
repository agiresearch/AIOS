from abc import ABC


class Communication(ABC):

    def send(self, *args, **kwargs):
        pass

    def receive(self, *args, **kwargs):
        pass
