import torch
import re
import time
from abc import ABC, abstractmethod

from openai import OpenAI
import google.generativeai as genai
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import BedrockChat

import os
import json

from src.llms.llm_config import LLMMeta

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)


from src.utils.utils import get_from_env

class SubKernel(ABC):
    @abstractmethod
    def load_llm_and_tokenizer(self):
        raise NotImplementedError

    @abstractmethod
    def call_process(self, prompt: str):
        raise NotImplementedError

class HuggingFaceSubKernel(SubKernel):
    def __init__(self, config: LLMMeta, max_gpu_memory: dict = None, eval_device: str = None, max_new_tokens: int = 256):
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device
        self.config = config

        self.load_llm_and_tokenizer()
        self.MAX_NEW_TOKENS = max_new_tokens
        print("AIOS LLM successfully loaded. ")

    def _convert_map(self, map: dict) -> dict:
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def load_llm_and_tokenizer(self):
        self.max_gpu_memory = self._convert_map(self.max_gpu_memory)
        hf_token, cache_dir = None, None

        self.model = AutoModelForCausalLM.from_pretrained(
            self.config.name,
            use_auth_token = hf_token,
            cache_dir = cache_dir,
            torch_dtype=torch.float16,
            device_map="auto",
            max_memory = self.max_gpu_memory
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.name,
            use_auth_token = hf_token,
            cache_dir = cache_dir
        )

        self.tokenizer.pad_token_id = self.model.config.eos_token_id

    def call_process(self, prompt: str):
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt")
        attention_mask = input_ids != self.tokenizer.pad_token_id
        input_ids = input_ids.to(self.eval_device)

        output_ids = self.model.generate(
            input_ids = input_ids,
            attention_mask = attention_mask,
            max_new_tokens = self.MAX_NEW_TOKENS,
            num_return_sequences=1,
            temperature = 0.0
        )

        outputs = self.tokenizer.decode(output_ids[0], skip_special_tokens=True)

        return outputs[len(prompt)+1: ]

class OpenAISubKernel(SubKernel):
    def __init__(self, config: LLMMeta):
        self.config = config

        self.load_llm_and_tokenizer()


    def load_llm_and_tokenizer(self):
        self.model = OpenAI()
        self.tokenizer = None

    def call_process(self, prompt: str):
        response = self.model.chat.completions.create(
            model=self.config.name,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content

class GeminiSubKernel(SubKernel):
    def __init__(self, config: LLMMeta):
        self.config = config

        self.load_llm_and_tokenizer()


    def load_llm_and_tokenizer(self):
        genai.configure(api_key=get_from_env("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel(self.config.name)
        self.tokenizer = None

    def call_process(self, prompt: str):
        outputs = self.model.generate_content(prompt)
        try:
            return outputs.text
        except IndexError:
            return f"{self.config.name} can not generate a valid result, please try again"

class BedrockSubKernel(SubKernel):
    def __init__(self, config: LLMMeta):
        self.config = config

        self.load_llm_and_tokenizer()


    def load_llm_and_tokenizer(self):
        model_id = self.model_name.split("/")[-1]
        self.model = BedrockChat(
            model_id=model_id,
            model_kwargs={
                'temperature': 0.0
            }
        )
        self.tokenizer = None

    def call_process(self, prompt: str):
        chat_template = ChatPromptTemplate.from_messages([
            ("user", "{prompt}")
        ])

        messages = chat_template.format_messages(prompt=prompt)
        response = self.model(messages)
        return response.content

class LLMKernel:
    def __init__(self, llm_name: str, *args, **kwargs):
        self._config = LLMMeta.get_model_from_datasource(llm_name)

        match self._config.name:
            case self._config.name if 'huggingface' in self._config.name:
                self.subkernel = HuggingFaceSubKernel(self._config,*args, **kwargs)
            case self._config.name if 'bedrock' in self._config.name:
                self.subkernel = BedrockSubKernel(self._config,*args, **kwargs)
            case self._config.name if 'gpt' in self._config.name:
                self.subkernel = OpenAISubKernel(self._config,*args, **kwargs)
            case self._config.name if 'gemini' in self._config.name:
                self.subkernel = GeminiSubKernel(self._config,*args, **kwargs)
            case self._config.name if 'claude' in self._config.name:
                pass
            case _:
                raise NotImplementedError

    def address_request(self, prompt: str):
        return self.subkernel.call_process(prompt)



if __name__ == "__main__":
    llm_type = "gemini-pro"
    llm = LLMKernel(llm_type)
    prompt = "Craft a tale about a valiant warrior on a quest to uncover priceless treasures hidden within a mystical island."
    print(llm.address_request(prompt))
