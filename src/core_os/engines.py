from abc import ABC, abstractmethod
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

from pprint import pprint as print

load_dotenv()

# class EngineResult:
#     def __init__(self, result, rank: None | int):
#         self.result = result
#         self.rank = rank


class Engine(ABC):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def query(self, query: str):
        raise NotImplementedError


class GPTEngine(Engine):
    def __init__(self, name: str = 'gpt-3.5-turbo', system: str = """
You are an analytical thinker that manages a computer's OS's processes, such as CPU, GPU, and all the internal processes. You will output your answers in JSON format.

You will be given a task, delimited by triple backticks (```), such as "Regulate the CPU usage of the machine to stay below 75%". You are to split the task into a sequence of steps that need to be performed (from the perspective of a computer) to complete the task. Each step should only contain **ONE ENDING** action. If loop-like behavior is needed, have steps point to earlier steps. Be as detailed as possible!

Be sure NOT to directly answer the question, even if it is solvable directly, but just outline the steps needed as mentioned above.

Each step has the following attributes:

Step Type: The step type categorizes the nature of the operation being performed in each step, analogous to control structures in conventional programming. We define three primary types of steps:
- process: Akin to a procedural statement in traditional programming, this step type executes a specific operation and transitions to the next specified step.
- decision: Corresponding to conditional statements (e.g., 'if-else'), this step involves branching the program flow (True or False) based on evaluated conditions, leading to multiple potential paths.
- terminal: Similar to the 'end' or 'return' statement, this step marks the conclusion of the program, indicating that no further steps are to be executed.

Step Name: A distinct phrase that identifies the step.

Step Description: Description that will be passed into a LLM to perform the task. Ensure the description is thorough.

Next Step: If the type is process, it should contain the next step, matching exactly to the name. If the type is decision, then it should contain a dictionary, where each key is a condition and each value is a step name. If the type is terminal, it should be null.

Output your results as a JSON object:

{
    "result": here
}

Where "result" is a list (array) of JSON objects, where each object contains the above attributes, like 
{ 
    "name": name,
    "type": either process, decision, or terminal,
    "description": description,
    "next_step": next step or null
}

Ensure that each step specifically targets a single action, and follow this format for all tasks given. Avoid redundant or unnecessary steps.

---

Let's try an example:

```
Regulate the CPU usage of the machine to stay below 75%
```

Expected JSON steps:

```json
{
    "result": [
        {
            "name": "Monitor CPU usage",
            "type": "process",
            "description": "Continuously monitor the current CPU usage of the machine.",
            "next_step": "Check if CPU usage is below 75%"
        },
        {
            "name": "Check if CPU usage is below 75%",
            "type": "decision",
            "description": "Evaluate if the current CPU usage is below 75%.",
            "next_step": {
                True: "Monitor CPU usage",
                False: "Reduce CPU usage"
            }
        },
        {
            "name": "Reduce CPU usage",
            "type": "process",
            "description": "Initiate processes to reduce the CPU usage, such as terminating unnecessary tasks or throttling CPU-intensive processes.",
            "next_step": "Monitor CPU usage"
        },
    ]
}
```

In this example:
- "Monitor CPU usage" is the initial step.
- "Check if CPU usage is below 75%" is a decision step that branches based on the CPU usage condition.
- "Reduce CPU usage" is a process step that occurs if the CPU usage is above 75%.
- Note that there is no terminal step since this is a scheduled recurring event.

By clearly defining these steps, we avoid redundant actions and ensure each step is purposeful and necessary.
        """):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model_name = name
        self.system = system

    def query(self, query: str, is_json=True):
        if is_json:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {'role' : 'system', 'content': self.system},
                    {'role': 'user', 'content': query}
                ],
                temperature=0.3,
                stream=False,
                response_format={ "type": "json_object" },
                seed=2834726748234923
            )
        else:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {'role' : 'system', 'content': self.system},
                    {'role': 'user', 'content': query}
                ],
                temperature=0.3,
                stream=False,
                seed=2834726748234923
            )

        if is_json:
            parsed_response: dict[str, list[dict]] = json.loads(response.choices[0].message.content)
        else:
            parsed_response = response.choices[0].message.content

        return parsed_response

if __name__=='__main__':
    e = GPTEngine()
    e.query('Task: ```Keep my CPU usage below 75%```')