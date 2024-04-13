import re
from .base_llm import BaseLLMKernel
import time
from openai import OpenAI

class GPTLLM(BaseLLMKernel):

    def load_llm_and_tokenizer(self) -> None:
        self.model = OpenAI()
        self.tokenizer = None

    def gpt_process(self,
            agent_process,
            temperature=0.0
        ):
        assert re.search(r'gpt', self.model_name, re.IGNORECASE)
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        prompt = agent_process.prompt,
        print(f"Prompt: {prompt}")
        response = self.model.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        time.sleep(2) # set according to your request per minite
        agent_process.set_response(response.choices[0].message.content)
        agent_process.set_status("done")
        agent_process.set_end_time(time.time())
        return