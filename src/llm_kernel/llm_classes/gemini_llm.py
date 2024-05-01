import re

from .base_llm import BaseLLMKernel
import time
from ...utils.utils import get_from_env
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
        assert re.search(r'gemini', self.model_name, re.IGNORECASE)
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.prompt
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )
        outputs = self.model.generate_content(
            prompt
        )
        try:
            result = outputs.candidates[0].content.parts[0].text
            agent_process.set_response(result)
        except IndexError:
            raise IndexError(f"{self.model_name} can not generate a valid result, please try again")
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
