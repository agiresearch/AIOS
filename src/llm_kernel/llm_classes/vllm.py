import re
from .base_llm import BaseLLMKernel
import time

# could be dynamically imported similar to other models
from openai import OpenAI
from .constant import MODEL_CLASS

from pyopenagi.utils.chat_template import Response
from ...utils.utils import get_from_env

from transformers import AutoTokenizer

class vLLM(BaseLLMKernel):

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
        """ fetch the model from huggingface and run it """
        self.max_gpu_memory = self.convert_map(self.max_gpu_memory)

        self.auth_token = get_from_env("HF_AUTH_TOKENS")

        try:
            import vllm
        except ImportError:
            raise ImportError(
                "Could not import vllm python package. "
                "Please install it with `pip install vllm`."
            )

        """ only casual lms for now """
        self.model = vllm.LLM(
            model = self.model_name
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            use_auth_token = self.auth_token
        )
        self.tokenizer.pad_token_id = self.tokenizer.eos_token_id

    def process(self,
                agent_process,
                temperature=0.0) -> None:
        agent_process.set_status("executing")
        agent_process.set_start_time(time.time())
        self.logger.log(
            f"{agent_process.agent_name} is switched to executing.\n",
            level = "executing"
        )

        messages = agent_process.query.messages
        # print(messages)
        tools = agent_process.query.tools

        if agent_process.query.tools:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tools = tools,
                tokenize = False
            )
        else:
            prompt = self.tokenizer.apply_chat_template(
                messages,
                tokenize = False
            )

        result = self.model.generate(
            prompt
        )[0].outputs[0].text
            # print(inputs)
            # input_ids = inputs["input_ids"][0]
            # attention_mask = inputs["attention_mask"][0]
        agent_process.set_response(
            Response(
                response_message=result
            )
        )
        agent_process.set_status("done")

        agent_process.set_end_time(time.time())
