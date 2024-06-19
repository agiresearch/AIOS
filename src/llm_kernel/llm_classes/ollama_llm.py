# wrapper around ollama for LLMs

import re
from .base_llm import BaseLLMKernel
import time
import ollama

from transformers import AutoTokenizer

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
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )
        response = ollama.chat(
            model=self.model_name.split("/")[-1],
            messages=messages
        )
        agent_process.set_response(
            Response(
                response_message = response['message']['content']
            )
        )
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
