from abc import ABC, abstractmethod

class BaseKernel(ABC):
    @abstractmethod
    def __init__(self, name: str):
        raise NotImplementedError
    
    @abstractmethod
    def execute(self, phrase: str):
        raise NotImplementedError

    @abstractmethod
    def play(self):
        raise NotImplementedError
    
    @abstractmethod
    def pause(self):
        raise NotImplementedError
    
    @abstractmethod
    def end(self):
        raise NotImplementedError
    
