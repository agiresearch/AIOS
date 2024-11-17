import re
import time

# could be dynamically imported similar to other models
from openai import OpenAI

from cerebrum.llm.base import BaseLLM
from cerebrum.utils.chat import Query, Response

import openai
import json


class GPTLLM(BaseLLM):
    def __init__(self, llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 1024,):
        super().__init__(llm_name,
                         max_gpu_memory,
                         eval_device,
                         max_new_tokens,)

    def load_llm_and_tokenizer(self) -> None:
        self.model = OpenAI()
        self.tokenizer = None

    def parse_tool_calls(self, tool_calls):
        if tool_calls:
            parsed_tool_calls = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                parsed_tool_calls.append(
                    {
                        "name": function_name,
                        "parameters": function_args,
                        "type": tool_call.type,
                        "id": tool_call.id
                    }
                )
            return parsed_tool_calls
        return None

    def process(self, query: Query):
        # ensures the model is the current one
        assert re.search(r'gpt', self.model_name, re.IGNORECASE)

        """ wrapper around openai api """
        # agent_process.set_status("executing")
        # agent_process.set_start_time(time.time())
        messages = query.messages
        # print(messages)
        # self.logger.log(
        #     f"{agent_process.agent_name} is switched to executing.\n",
        #     level = "executing"
        # )
        # time.sleep(10)
        try:
            response = self.model.chat.completions.create(
                model=self.model_name,
                messages=messages,
                tools=query.tools,
                # tool_choice = "required" if agent_process.query.tools else None,
                max_tokens=self.max_new_tokens,
                # response_format = {"type": "json_object"}
            )
            # print(response_message)
            response_message = response.choices[0].message.content
            # print(response_message)
            tool_calls = self.parse_tool_calls(
                response.choices[0].message.tool_calls
            )
            # print(tool_calls)
            # print(response.choices[0].message)
            return Response(
                response_message=response_message,
                tool_calls=tool_calls
            )
        except openai.APIConnectionError as e:
            return Response(
                response_message=f"Server connection error: {e.__cause__}"
            )

        except openai.RateLimitError as e:
            return Response(
                response_message=f"OpenAI RATE LIMIT error {e.status_code}: (e.response)"
            )
        except openai.APIStatusError as e:
            return Response(
                response_message=f"OpenAI STATUS error {e.status_code}: (e.response)"
            )
        except openai.BadRequestError as e:
            return Response(
                response_message=f"OpenAI BAD REQUEST error {e.status_code}: (e.response)"
            )
        except Exception as e:
            return Response(
                response_message=f"An unexpected error occurred: {e}"
            )
