# wrapper around ollama for LLMs

import re
from .base_llm import BaseLLMKernel
import time
import ollama


from pyopenagi.utils.chat_template import Response

class OllamaLLM(BaseLLMKernel):

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
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )

        # print(f"Current messages: {messages}, use tools: {True if tools else False}")

        if tools:
            messages = self.tool_calling_input_format(messages, tools)
            response = ollama.chat(
                model=self.model_name.split("/")[-1],
                messages=messages
            )

            # print(response)
            tool_calls = self.tool_calling_output_format(
                response["message"]["content"]
            )

            if tool_calls:
                # print("Match json format")
                # print(f"Matched tool call is: {tool_calls}")

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

        else:
            messages = self.tool_calling_input_format(messages, tools)
            response = ollama.chat(
                model=self.model_name.split("/")[-1],
                messages=messages
            )
            # print(response)
            agent_process.set_response(
                Response(
                    response_message = response['message']['content']
                )
            )

        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
