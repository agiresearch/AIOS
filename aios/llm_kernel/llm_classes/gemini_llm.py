# wrapper around gemini from google for LLMs

import re

from .base_llm import BaseLLMKernel
import time
from ...utils.utils import get_from_env

from pyopenagi.utils.chat_template import Response
class GeminiLLM(BaseLLMKernel):
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
        assert self.model_name == "gemini-pro"
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

    def process(self,
                agent_process,
                temperature=0.0) -> None:
        # ensures the model is the current one
        assert re.search(r'gemini', self.model_name, re.IGNORECASE)

        """ wrapper around functions"""

        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.message.prompt
        # TODO: add tool calling
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )

        # blocks this thread to allow execution of other threads
        time.sleep(2)

        outputs = self.model.generate_content(
            prompt
        )
        try:
            result = outputs.candidates[0].content.parts[0].text
            agent_process.set_response(
                Response(
                    response_message = result
                )
            )
        except IndexError:
            raise IndexError(f"{self.model_name} can not generate a valid result, please try again")
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
