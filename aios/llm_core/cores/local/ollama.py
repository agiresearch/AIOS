# wrapper around ollama for LLMs

import re
import time
import ollama

from aios.llm_core.cores.base import BaseLLM

from aios.utils import get_from_env

from cerebrum.llm.communication import Response


class OllamaLLM(BaseLLM):

    def __init__(
        self,
        llm_name: str,
        max_gpu_memory: dict = None,
        eval_device: str = None,
        max_new_tokens: int = 256,
        log_mode: str = "console",
        use_context_manager=False,
    ):
        super().__init__(
            llm_name,
            max_gpu_memory,
            eval_device,
            max_new_tokens,
            log_mode,
            use_context_manager
        )

    def load_llm_and_tokenizer(self) -> None:
        self.model = None
        self.tokenizer = None

    def address_syscall(self, llm_syscall, temperature=0.0):
        # ensures the models are from ollama
        assert re.search(r"ollama", self.model_name, re.IGNORECASE)

        """ simple wrapper around ollama functions """
        llm_syscall.set_status("executing")
        llm_syscall.set_start_time(time.time())
        messages = llm_syscall.query.messages
        tools = llm_syscall.query.tools
        message_return_type = llm_syscall.query.message_return_type
        self.logger.log(
            f"{llm_syscall.agent_name} is switched to executing.\n", level="executing"
        )

        # with and without overhead for tool handling
        if tools:
            messages = self.tool_calling_input_format(messages, tools)
            try:
                response = ollama.chat(
                    model=self.model_name.split("/")[-1], messages=messages
                )

                tool_calls = self.parse_tool_calls(response["message"]["content"])

                if tool_calls:
                    llm_syscall.set_response(
                        Response(
                            response_message=None, tool_calls=tool_calls, finished=True
                        )
                    )
                else:
                    llm_syscall.set_response(
                        Response(
                            response_message=response["message"]["content"],
                            finished=True,
                        )
                    )
            except Exception as e:
                llm_syscall.set_response(
                    Response(response_message=f"An unexpected error occurred: {e}"),
                    finished=True,
                )

        else:
            try:
                response = ollama.chat(
                    model=self.model_name.split("/")[-1],
                    messages=messages,
                    options=ollama.Options(num_predict=self.max_new_tokens),
                )
                result = response["message"]["content"]

                # print(f"***** original result: {result} *****")

                if message_return_type == "json":
                    result = self.parse_json_format(result)

                llm_syscall.set_response(
                    Response(response_message=result, finished=True)
                )

            except Exception as e:
                llm_syscall.set_response(
                    Response(
                        response_message=f"An unexpected error occurred: {e}",
                        finished=True,
                    )
                )

        llm_syscall.set_status("done")
        llm_syscall.set_end_time(time.time())
        return
