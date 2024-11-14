from abc import ABC
from typing import List

from pyopenagi.agents.experiment.standard.environment.environment import Environment


class CodeEnvironment(Environment, ABC):
    """
    Environment for code.
    """


class LocalCodeEnvironment(CodeEnvironment):
    """
    Local code environment.
    """

    def init_environment(self, requirement_list: List[str]):
        pass

    def step(self, code_block: str):
        pass


class DockerCodeEnvironment(CodeEnvironment):
    """
    Docker code environment.
    """

    def init_environment(self, *args, **kwargs):
        pass

    def step(self, *args, **kwargs):
        pass
