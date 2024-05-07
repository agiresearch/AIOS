import re
from .base_llm import BaseLLMKernel
import time
import ollama

class OllamaLLM(BaseLLMKernel):

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
        self.model_name = llm_name.split('/')[1]
        self.mode = 'ollama'

    def load_llm_and_tokenizer(self) -> None:
        self.model = None
        self.tokenizer = None


    def process(self,
            agent_process,
            temperature=0.0
        ):
        assert re.search(r'ollama', self.mode, re.IGNORECASE)
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.prompt
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )
        response = ollama.chat(model=self.model_name, messages=[
            {
                "role": "user", "content": prompt
            }
        ])
        agent_process.set_response(response['message']['content'])
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
