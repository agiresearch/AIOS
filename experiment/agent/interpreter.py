import os
import re

from interpreter import interpreter

from aios.sdk import prepare_framework, FrameworkType
from experiment.agent.experiment_agent import ExpirementAgent


class InterpreterAgent(ExpirementAgent):

    SYSTEM_PROMPT_WRITE = """\n You can try writing some code to solve the problem, but please note that you are not in the
    problem repository. Must write your final patch into patch.diff. If code is hard to run, just write the patch you
    think right. You should write patch.diff use Here Document, for example:
        cat <<EOF_59812759871 > patch.diff
        <patch content here>
        EOF_59812759871 \n"""

    SYSTEM_PROMPT = """\n You can try writing some code to solve the problem, but please note that you are not in the
    problem repository. Finally give me a patch that can be written into git diff file, format like this:
    ```patch
    patch content here
    ```
    """

    def __init__(self, on_aios: bool = True):
        if on_aios:
            prepare_framework(FrameworkType.OpenInterpreter)
        interpreter.messages = []
        interpreter.auto_run = True
        self.interpreter = interpreter

    def run(self, input_str: str):

        input_str += self.SYSTEM_PROMPT
        result = self.interpreter.chat(input_str)

        try:
            result = result[0] if isinstance(result, list) else result
        except IndexError:
            return str(result)

        try:
            # read model output
            current_directory = os.getcwd()
            diff_path = os.path.join(current_directory, "patch.diff")

            with open(diff_path, 'r') as file:
                diff_content = file.read()
                result_content = f"```patch {diff_content}```"

            os.remove(diff_path)

        except Exception:
            result_content = result["content"]
            # content_lines = result_content.split("\n")
            # result_content = "\n".join(content_lines[1:-1])
            # result_content = f"```patch {result_content}```"

        print(f"Interterper result is: {result_content} \n")
        return result_content


class InterpreterAgentHumanEval(ExpirementAgent):

    SYSTEM_PROMPT = """You will receive a function definition and comments. You need to help me complete this function.

    Give me final output in the format:
    <FINAL ANSWER>
        YOUR FINAL ANSWER (YOUR FINAL ANSWER must be a piece of code that you want to add. The final result must remove
         the function definition and function description provided in the problem statement, as well as any unit test
         code you added.)
    </FINAL ANSWER> """

    def __init__(self, on_aios: bool = True):
        if on_aios:
            prepare_framework(FrameworkType.OpenInterpreter)
        interpreter.messages = []
        interpreter.auto_run = True
        self.interpreter = interpreter

    def run(self, input_str: str):
        input_str += self.SYSTEM_PROMPT
        result = self.interpreter.chat(input_str)

        try:
            result = result[0] if isinstance(result, list) else result
            if isinstance(result, list):
                result = result[0]
        except IndexError as e:
            print(f"IndexError: {e}")
            return str(result)

        print(f"Interterper result is: {result} \n")
        if isinstance(result, dict):
            result_content = result["content"]

            if result["type"] == "code":
                result_content = f"""
                    ```python
                    {result_content}
                    ```"""
            elif result["type"] == "message":
                match = re.search(r'<FINAL ANSWER>\s*([\s\S]*?)</FINAL ANSWER>', result_content)
                if match:
                    result_content = match.group(1)
        else:
            result_content = result

        print(f"Interterper result is: {result_content} \n")
        return result_content
