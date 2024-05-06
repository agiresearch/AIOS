import re
from .base_llm import BaseLLMKernel
import time
from openai import OpenAI

class GPTLLM(BaseLLMKernel):

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
        self.model = OpenAI()
        self.tokenizer = None

    def process(self,
            agent_process,
            temperature=0.0
        ):
        assert re.search(r'gpt', self.model_name, re.IGNORECASE)
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.prompt
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        agent_process.set_response(response.choices[0].message.content)
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return
