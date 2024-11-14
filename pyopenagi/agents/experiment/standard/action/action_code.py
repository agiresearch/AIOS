from pyopenagi.agents.experiment.standard.action.action import Action
from pyopenagi.agents.experiment.standard.environment.code_environment import CodeEnvironment

CODE_PROMPT = """You can write code to solve problem. If you want to write code to solve problem, surrounding your
code with a code block. A code block should like:

```python
def main():
    print("hello")

if __name__ == '__main__':
    main()
```

If additional dependencies are required, please provid the command install them, format like:

```requirement
pip install torch
pip install numpy
```
"""


class ActionCode(Action):
    """
    Action responsible for writing code to solve problem.
    """

    def __init__(self, environment: CodeEnvironment):
        super().__init__()
        self.type = "CODE"
        self.environment = environment

    def __call__(self, code: str, requirements: str):
        """
        Execute code with requirements.
        """
        return self.execute_code(code, requirements)

    def execute_code(self, code: str, requirements: str):
        """
        Execute code with requirements.

        Args:
            code (str): The code to be executed.
            requirements (str): The command to install additional dependencies.

        Returns:
            str: The result of the code execution.
        """

        init_err = self.environment.init_environment(requirements)
        if init_err:
            # If init error, return error msg
            return init_err

        exec_res = self.environment.step(code)
        return exec_res

    def format_prompt(self):
        return {
            "name": "code",
            "description": CODE_PROMPT
        }
