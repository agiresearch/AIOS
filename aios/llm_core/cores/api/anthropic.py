import re
import json
import time
import anthropic
from typing import List, Dict, Any

from aios.llm_core.cores.base import BaseLLM

from cerebrum.llm.communication import Response


class ClaudeLLM(BaseLLM):
    """
    ClaudeLLM class for interacting with Anthropic's Claude models.

    This class provides methods for processing queries using Claude models,
    including handling of tool calls and message formatting.

    Attributes:
        model (anthropic.Anthropic): The Anthropic client for API calls.
        tokenizer (None): Placeholder for tokenizer, not used in this implementation.
    """

    def __init__(
        self,
        llm_name: str,
        max_gpu_memory: Dict[int, str] = None,
        eval_device: str = None,
        max_new_tokens: int = 256,
        log_mode: str = "console",
        use_context_manager: bool = False,
    ):
        """
        Initialize the ClaudeLLM instance.

        Args:
            llm_name (str): Name of the Claude model to use.
            max_gpu_memory (Dict[int, str], optional): GPU memory configuration.
            eval_device (str, optional): Device for evaluation.
            max_new_tokens (int, optional): Maximum number of new tokens to generate.
            log_mode (str, optional): Logging mode, defaults to "console".
        """
        super().__init__(
            llm_name,
            max_gpu_memory=max_gpu_memory,
            eval_device=eval_device,
            max_new_tokens=max_new_tokens,
            log_mode=log_mode,
            use_context_manager=use_context_manager,
        )

    def load_llm_and_tokenizer(self) -> None:
        """
        Load the Anthropic client for API calls.
        """
        self.model = anthropic.Anthropic()
        self.tokenizer = None

    def convert_tools(self, tools):
        anthropic_tools = []
        # print(tools)
        for tool in tools:
            anthropic_tool = tool["function"]
            anthropic_tool["name"] = "--".join(anthropic_tool["name"].split("/"))
            anthropic_tool["input_schema"] = anthropic_tool["parameters"]
            anthropic_tool.pop("parameters")
            anthropic_tools.append(anthropic_tool)
        # print(anthropic_tools)
        return anthropic_tools

    def parse_tool_calls(self, tool_calls):
        if tool_calls:
            parsed_tool_calls = []
            for tool_call in tool_calls:
                function_name = tool_call.name
                function_name = "/".join(function_name.split("--"))
                # function_args = json.loads(tool_call.input)
                function_args = tool_call.input
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

    def address_syscall(self, llm_syscall, temperature: float = 0.0) -> None:
        """
        Process a request_data using the Claude model.

        Args:
            agent_request (Any): The agent process containing the request_data and tools.
            temperature (float, optional): Sampling temperature for generation.

        Raises:
            AssertionError: If the model name doesn't contain 'claude'.
            anthropic.APIError: If there's an error with the Anthropic API call.
            Exception: For any other unexpected errors.
        """
        assert re.search(
            r"claude", self.model_name, re.IGNORECASE
        ), "Model name must contain 'claude'"
        llm_syscall.set_status("executing")
        llm_syscall.set_start_time(time.time())
        messages = llm_syscall.query.messages
        tools = llm_syscall.query.tools

        self.logger.log(f"{messages}", level="info")
        self.logger.log(
            f"{llm_syscall.agent_name} is switched to executing.", level="executing"
        )

        if tools:
            # messages = self.tool_calling_input_format(messages, tools)
            tools = self.convert_tools(tools)

        anthropic_messages = self._convert_to_anthropic_messages(messages)
        self.logger.log(f"{anthropic_messages}", level="info")

        try:
            if tools:
                response = self.model.messages.create(
                    model=self.model_name,
                    messages=anthropic_messages,
                    max_tokens=self.max_new_tokens,
                    temperature=temperature,
                    tools=tools,
                )
                response_message = response.content[0].text

                tool_call_messages = response.content[1]

                if tool_call_messages:
                    response_message = None
                    if not isinstance(tool_call_messages, list):
                        tool_call_messages = [tool_call_messages]

                tool_calls = (
                    self.parse_tool_calls(tool_call_messages) if tools else None
                )

            else:
                response = self.model.messages.create(
                    model=self.model_name,
                    messages=anthropic_messages,
                    max_tokens=self.max_new_tokens,
                    temperature=temperature,
                )

                response_message = response.content[0].text

                tool_calls = None

            response = Response(
                response_message=response_message, tool_calls=tool_calls, finished=True
            )

            # agent_request.set_response(
            #     Response(
            #         response_message=response_message,
            #         tool_calls=tool_calls
            #     )
            # )
        except anthropic.APIError as e:
            error_message = f"Anthropic API error: {str(e)}"
            self.logger.log(error_message, level="warning")

            response = Response(response_message=f"Error: {str(e)}", tool_calls=None)

            # agent_request.set_response(
            #     Response(
            #         response_message=f"Error: {str(e)}",
            #         tool_calls=None
            #     )
            # )

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            self.logger.log(error_message, level="warning")
            # agent_request.set_response(
            #     Response(
            #         response_message=f"Unexpected error: {str(e)}",
            #         tool_calls=None
            #     )
            # )
            response = Response(
                response_message=f"Unexpected error: {str(e)}",
                tool_calls=None,
                finished=True,
            )

        return response
        # agent_request.set_status("done")
        # agent_request.set_end_time(time.time())

    def _convert_to_anthropic_messages(
        self, messages: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """
        Convert messages to the format expected by the Anthropic API.

        Args:
            messages (List[Dict[str, str]]): Original messages.

        Returns:
            List[Dict[str, str]]: Converted messages for Anthropic API.
        """
        anthropic_messages = []
        for message in messages:
            if message["role"] == "system":
                anthropic_messages.append(
                    {"role": "user", "content": f"System: {message['content']}"}
                )
                anthropic_messages.append(
                    {
                        "role": "assistant",
                        "content": "Understood. I will follow these instructions.",
                    }
                )
            else:
                anthropic_messages.append(
                    {
                        "role": "user" if message["role"] == "user" else "assistant",
                        "content": message["content"],
                    }
                )
        return anthropic_messages

    def tool_calling_output_format(
        self, tool_calling_messages: str
    ) -> List[Dict[str, Any]]:
        """
        Parse the tool calling output from the model's response.

        Args:
            tool_calling_messages (str): The model's response containing tool calls.

        Returns:
            List[Dict[str, Any]]: Parsed tool calls, or None if parsing fails.
        """
        try:
            json_content = json.loads(tool_calling_messages)
            if (
                isinstance(json_content, list)
                and len(json_content) > 0
                and "name" in json_content[0]
            ):
                return json_content
        except json.JSONDecodeError:
            pass
        return super().tool_calling_output_format(tool_calling_messages)
