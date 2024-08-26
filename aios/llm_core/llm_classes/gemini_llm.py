# wrapper around gemini from google for LLMs

import re

from .base_llm import BaseLLM
import time
from ...utils.utils import get_from_env
import json

from pyopenagi.utils.chat_template import Response
class GeminiLLM(BaseLLM):
    def __init__(self, llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"):
        super().__init__(llm_name,
                         max_gpu_memory,
                         eval_device,
                         max_new_tokens,
                         log_mode)

    def load_llm_and_tokenizer(self) -> None:
        """ dynamic loading because the module is only needed for this case """
        assert re.search(r'gemini', self.model_name, re.IGNORECASE)
        try:
            import google.generativeai as genai
            gemini_api_key = get_from_env("GEMINI_API_KEY")
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel(self.model_name)
            self.tokenizer = None
        except ImportError:
            raise ImportError(
                "Could not import google.generativeai python package. "
                "Please install it with `pip install google-generativeai`."
            )

    def convert_messages(self, messages):
        if messages:
            gemini_messages = []
            for m in messages:
                gemini_messages.append(
                    {
                        "role": "user" if m["role"] in ["user", "system"] else "model",
                        "parts": {"text": m["content"]}
                    }
                )
        else:
            gemini_messages = None
        return gemini_messages

    def process(self,
                agent_process,
                temperature=0.0) -> None:
        # ensures the model is the current one

        """ wrapper around functions"""

        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        messages = agent_process.query.messages
        tools = agent_process.query.tools
        message_return_type = agent_process.query.message_return_type

        if tools:
            messages = self.tool_calling_input_format(messages, tools)

        # convert role to fit the gemini role types
        messages = self.convert_messages(
            messages=messages,
        )

        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )

        outputs = self.model.generate_content(
            json.dumps({"contents": messages})
        )

        try:
            result = outputs.candidates[0].content.parts[0].text
            if tools:
                tool_calls = self.parse_tool_calls(result)
                if tool_calls:
                    agent_process.set_response(
                        Response(
                            response_message=None,
                            tool_calls=tool_calls
                        )
                    )
                else:
                    agent_process.set_response(
                        Response(
                            response_message=result,
                        )
                    )
            else:
                if message_return_type == "json":
                    result = self.parse_json_format(result)
                agent_process.set_response(
                    Response(
                        response_message=result,
                    )
                )
        except IndexError:
            raise IndexError(f"{self.model_name} can not generate a valid result, please try again")
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
