import subprocess
import sys
import tempfile
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
        """
        Initialize the environment with requirements.

        Args:
            requirement_list (List[str]): The list of requirement commands(Format like `pip install numpy`).

        """
        if len(requirement_list) == 0:
            return

        for requirement in requirement_list:
            if "pip install" in requirement:
                package = requirement.split(" ")[-1]
            else:
                package = requirement
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"Run command successfully: `pip install {package}`")
            except subprocess.CalledProcessError as e:
                err_msg = (f"Run command failed: `pip install {package}`\n"
                           f"Return code: {e.returncode}\n"
                           f"Error message: {e.stderr}\n"
                           f"Output: {e.stdout}")
                print(err_msg)
                return err_msg

    def step(self, code_block: str, language: str = "python"):
        # Create temp file, write python code into temp file, then execute it
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=True) as temp_file:
            temp_file.write(code_block)
            try:
                exec_res = subprocess.run(
                    ["python", temp_file.name],
                    capture_output=True,
                    text=True,
                    check=True)
                step_res = exec_res.stdout
            except subprocess.CalledProcessError as e:
                err_msg = (f"Run python code failed:`\n"
                           f"Return code: {e.returncode}\n"
                           f"Error message: {e.stderr}\n"
                           f"Output: {e.stdout}")
                step_res = err_msg
        return step_res


class DockerCodeEnvironment(CodeEnvironment):
    """
    Docker code environment.
    """

    def init_environment(self, *args, **kwargs):
        pass

    def step(self, *args, **kwargs):
        pass
