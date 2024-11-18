# wrapper around gemini from google for LLMs

import re
import time
import json

from cerebrum.llm.base import BaseLLM
from cerebrum.utils.chat import Query, Response
from cerebrum.utils.llm import get_from_env


class GeminiLLM(BaseLLM):
    def __init__(self, llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,):
        super().__init__(llm_name,
                         max_gpu_memory,
                         eval_device,
                         max_new_tokens,)

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

    def process(self, query: Query):
        # ensures the model is the current one
        """ wrapper around functions"""

        # agent_process.set_status("executing")
        # agent_process.set_start_time(time.time())
        messages = query.messages
        tools = query.tools
        message_return_type = query.message_return_type

        if tools:
            messages = self.tool_calling_input_format(messages, tools)

        # convert role to fit the gemini role types
        messages = self.convert_messages(
            messages=messages,
        )

        # self.logger.log(
        #     f"{agent_process.agent_name} is switched to executing.\n",
        #     level = "executing"
        # )

        outputs = self.model.generate_content(
            json.dumps({"contents": messages})
        )

        try:
            result = outputs.candidates[0].content.parts[0].text
            if tools:
                tool_calls = self.parse_tool_calls(result)
                if tool_calls:
                    return Response(
                        response_message=None,
                        tool_calls=tool_calls
                    )

                else:
                    return Response(
                        response_message=result,
                    )

            else:
                if message_return_type == "json":
                    result = self.parse_json_format(result)
                return Response(
                    response_message=result,
                )
        except IndexError:
            raise IndexError(
                f"{self.model_name} can not generate a valid result, please try again")
