from pyopenagi.agents.experiment.standard.action.action import Action
from pyopenagi.agents.experiment.standard.environment.code_environment import CodeEnvironment

CODE_PROMPT = """You can write code to solve problem. If you want to write code to solve problem, surrounding your
code with a code block. A perfect code should contains
- a function defination, like:
    def calculate(a: int, b: int):
    return a + b
- a call of function, like:
    a = 5
    b = 10
    result = calculate(a, b)
    print(f"Code execute result is: {result}")

A code block should like:
```python
def calculate(a: int, b: int):
    return a + b

a = 5
b = 10
print(f"Code execute result is: {calculate(a, b)}")
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
        code_str = (f"###############Code###############\n"
                    f"{code}\n"
                    f"###############Code###############\n"
                    f"Code execute result is :{exec_res}")
        return code_str, None

    def format_prompt(self):
        return {
            "name": "code",
            "description": CODE_PROMPT
        }

    @staticmethod
    def display():
        return True
