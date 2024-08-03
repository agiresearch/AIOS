import re
import json
import time
import anthropic
from typing import List, Dict, Any
from .base_llm import BaseLLM
from pyopenagi.utils.chat_template import Response

class ClaudeLLM(BaseLLM):
    """
    ClaudeLLM class for interacting with Anthropic's Claude models.

    This class provides methods for processing queries using Claude models,
    including handling of tool calls and message formatting.

    Attributes:
        model (anthropic.Anthropic): The Anthropic client for API calls.
        tokenizer (None): Placeholder for tokenizer, not used in this implementation.
    """

    def __init__(self, llm_name: str,
                 max_gpu_memory: Dict[int, str] = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"):
        """
        Initialize the ClaudeLLM instance.

        Args:
            llm_name (str): Name of the Claude model to use.
            max_gpu_memory (Dict[int, str], optional): GPU memory configuration.
            eval_device (str, optional): Device for evaluation.
            max_new_tokens (int, optional): Maximum number of new tokens to generate.
            log_mode (str, optional): Logging mode, defaults to "console".
        """
        super().__init__(llm_name,
                         max_gpu_memory=max_gpu_memory,
                         eval_device=eval_device,
                         max_new_tokens=max_new_tokens,
                         log_mode=log_mode)

    def load_llm_and_tokenizer(self) -> None:
        """
        Load the Anthropic client for API calls.
        """
        self.model = anthropic.Anthropic()
        self.tokenizer = None

    def process(self, agent_process: Any, temperature: float = 0.0) -> None:
        """
        Process a query using the Claude model.

        Args:
            agent_process (Any): The agent process containing the query and tools.
            temperature (float, optional): Sampling temperature for generation.

        Raises:
            AssertionError: If the model name doesn't contain 'claude'.
            anthropic.APIError: If there's an error with the Anthropic API call.
            Exception: For any other unexpected errors.
        """
        assert re.search(r'claude', self.model_name, re.IGNORECASE), "Model name must contain 'claude'"
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        messages = agent_process.query.messages
        tools = agent_process.query.tools

        self.logger.log(f"{messages}", level="info")
        self.logger.log(f"{agent_process.agent_name} is switched to executing.", level="executing")

        if tools:
            messages = self.tool_calling_input_format(messages, tools)

        anthropic_messages = self._convert_to_anthropic_messages(messages)
        self.logger.log(f"{anthropic_messages}", level="info")

        try:
            response = self.model.messages.create(
                model=self.model_name,
                messages=anthropic_messages,
                max_tokens=self.max_new_tokens,
                temperature=temperature
            )

            response_message = response.content[0].text
            self.logger.log(f"API Response: {response_message}", level="info")
            tool_calls = self.parse_tool_calls(response_message) if tools else None

            agent_process.set_response(
                Response(
                    response_message=response_message,
                    tool_calls=tool_calls
                )
            )
        except anthropic.APIError as e:
            error_message = f"Anthropic API error: {str(e)}"
            self.logger.log(error_message, level="warning")
            agent_process.set_response(
                Response(
                    response_message=f"Error: {str(e)}",
                    tool_calls=None
                )
            )
        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            self.logger.log(error_message, level="warning")
            agent_process.set_response(
                Response(
                    response_message=f"Unexpected error: {str(e)}",
                    tool_calls=None
                )
            )

        agent_process.set_status("done")
        agent_process.set_end_time(time.time())

    def _convert_to_anthropic_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Convert messages to the format expected by the Anthropic API.

        Args:
            messages (List[Dict[str, str]]): Original messages.

        Returns:
            List[Dict[str, str]]: Converted messages for Anthropic API.
        """
        anthropic_messages = []
        for message in messages:
            if message['role'] == 'system':
                anthropic_messages.append({"role": "user", "content": f"System: {message['content']}"})
                anthropic_messages.append({"role": "assistant", "content": "Understood. I will follow these instructions."})
            else:
                anthropic_messages.append({
                    "role": "user" if message['role'] == 'user' else "assistant",
                    "content": message['content']
                })
        return anthropic_messages

    def tool_calling_output_format(self, tool_calling_messages: str) -> List[Dict[str, Any]]:
        """
        Parse the tool calling output from the model's response.

        Args:
            tool_calling_messages (str): The model's response containing tool calls.

        Returns:
            List[Dict[str, Any]]: Parsed tool calls, or None if parsing fails.
        """
        try:
            json_content = json.loads(tool_calling_messages)
            if isinstance(json_content, list) and len(json_content) > 0 and 'name' in json_content[0]:
                return json_content
        except json.JSONDecodeError:
            pass
        return super().tool_calling_output_format(tool_calling_messages)
