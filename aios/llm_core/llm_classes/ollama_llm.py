# wrapper around ollama for LLMs

import re
from .base_llm import BaseLLM
import time
import ollama

from pyopenagi.utils.chat_template import Response
class OllamaLLM(BaseLLM):

    def __init__(self, llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"):
        super().__init__(
            llm_name,
            max_gpu_memory,
            eval_device,
            max_new_tokens,
            log_mode
        )

    def load_llm_and_tokenizer(self) -> None:
        self.model = None
        self.tokenizer = None

    def process(self,
            agent_process,
            temperature=0.0
        ):
        # ensures the models are from ollama
        assert re.search(r'ollama', self.model_name, re.IGNORECASE)

        """ simple wrapper around ollama functions """
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        messages = agent_process.query.messages
        tools = agent_process.query.tools
        message_return_type = agent_process.query.message_return_type
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )

        if tools:
            messages = self.tool_calling_input_format(messages, tools)
            try:
                response = ollama.chat(
                    model=self.model_name.split("/")[-1],
                    messages=messages
                )

                tool_calls = self.parse_tool_calls(
                    response["message"]["content"]
                )

                if tool_calls:
                    agent_process.set_response(
                        Response(
                            response_message = None,
                            tool_calls = tool_calls
                        )
                    )
                else:
                    agent_process.set_response(
                        Response(
                            response_message = response['message']['content']
                        )
                    )
            except Exception as e:
                agent_process.set_response(
                    Response(
                        response_message = f"An unexpected error occurred: {e}"
                    )
                )

        else:
            try:
                response = ollama.chat(
                    model=self.model_name.split("/")[-1],
                    messages=messages,
                    options= ollama.Options(
                        num_predict=self.max_new_tokens
                    )
                )
                result = response['message']['content']

                # print(f"***** original result: {result} *****")

                if message_return_type == "json":
                    result = self.parse_json_format(result)

                agent_process.set_response(
                    Response(
                        response_message = result
                    )
                )

            except Exception as e:
                agent_process.set_response(
                    Response(
                        response_message = f"An unexpected error occurred: {e}"
                    )
                )

        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
