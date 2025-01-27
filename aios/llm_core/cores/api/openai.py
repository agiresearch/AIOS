import re
import time
import json

from openai import OpenAI, APIConnectionError, RateLimitError, BadRequestError, APIStatusError

from aios.llm_core.cores.base import BaseLLM

from cerebrum.llm.communication import Response


class GPTLLM(BaseLLM):

    def __init__(
        self,
        llm_name: str,
        max_gpu_memory: dict = None,
        eval_device: str = None,
        max_new_tokens: int = 1024,
        log_mode: str = "console",
        use_context_manager: bool = False,
    ):
        super().__init__(
            llm_name,
            max_gpu_memory,
            eval_device,
            max_new_tokens,
            log_mode,
            use_context_manager,
        )

    def load_llm_and_tokenizer(self) -> None:
        self.model = OpenAI()
        self.tokenizer = None

    def parse_tool_calls(self, tool_calls):
        if tool_calls:
            parsed_tool_calls = []
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_name = "/".join(function_name.split("--"))
                function_args = json.loads(tool_call.function.arguments)
                parsed_tool_calls.append(
                    {
                        "name": function_name,
                        "parameters": function_args,
                        "type": tool_call.type,
                        "id": tool_call.id,
                    }
                )
            return parsed_tool_calls
        return None
    
    def convert_tools(self, tools):
        for tool in tools:
            tool["function"]["name"] = "--".join(tool["function"]["name"].split("/"))
        return tools

    def address_syscall(self, llm_syscall, temperature=0.0):
        # ensures the model is the current one
        assert re.search(r"gpt", self.model_name, re.IGNORECASE)

        """ wrapper around openai api """
        llm_syscall.set_status("executing")
        llm_syscall.set_start_time(time.time())

        try:
            if self.use_context_manager:
                response = self.llm_generate(llm_syscall)
            else:
                query = llm_syscall.query
                if query.tools:
                    query.tools = self.convert_tools(query.tools)
               
                response = self.model.chat.completions.create(
                    model=self.model_name,
                    messages=query.messages,
                    tools=query.tools,
                    # tool_choice = "required" if agent_request.request_data.tools else None,
                    max_tokens=self.max_new_tokens,
                )

                response_message = response.choices[0].message.content
                
                # print(response_message)
                tool_calls = self.parse_tool_calls(
                    response.choices[0].message.tool_calls
                )
                
                response = Response(
                    response_message=response_message,
                    tool_calls=tool_calls,
                    finished=True,
                )
                # print(response)

        except APIConnectionError as e:
            response = Response(
                response_message=f"Server connection error: {e.__cause__}",
            )

        except RateLimitError as e:
            response = Response(
                response_message=f"OpenAI RATE LIMIT error {e.status_code}: (e.response)",
                finished=True
            )

        except APIStatusError as e:
            response = Response(
                response_message=f"OpenAI STATUS error {e.status_code}: (e.response)",
                finished=True
            )

        except BadRequestError as e:
            response = Response(
                response_message=f"OpenAI BAD REQUEST error {e.status_code}: (e.response)",
                finished=True
            )

        except Exception as e:
            response = Response(response_message=f"An unexpected error occurred: {e}",finished=True)

        return response

    def llm_generate(self, llm_syscall, temperature=0.0):
        query = llm_syscall.query
        if self.context_manager.check_restoration(llm_syscall.get_pid()):
            restored_context = self.context_manager.gen_recover(llm_syscall.get_pid())

        start_time = time.time()
        stream = self.model.chat.completions.create(
            model=self.model_name,
            messages=query.messages
            + [{"role": "assistant", "content": "" + restored_context}],
            stream=True,
            tools=query.tools,
            max_tokens=self.max_new_tokens,
        )

        result = ""
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                result += chunk.choices[0].delta.content
            end_time = time.time()
            if end_time - start_time >= llm_syscall.get_time_limit():
                self.context_manager.gen_snapshot(result)
                response = Response(response_message=result, finished=False)
                return response
