from abc import ABC, abstractmethod


class Environment(ABC):
    """
    Environment abstract base class. The environment is the foundation for the agent to execute actions.
    """

    @abstractmethod
    def init_environment(self, *args, **kwargs):
        """Init environment, prepare something required"""
        pass

    @abstractmethod
    def step(self, *args, **kwargs):
        """Take a step in the environment"""
        pass
