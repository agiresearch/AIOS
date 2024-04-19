from openai import OpenAI
import os
import json
import re
import time
from datetime import datetime
from src.context.simple_context import SimpleContextManager
import logging
from abc import ABC, abstractmethod

from src.utils.logger import LLMKernelLogger


class BaseLLMKernel(ABC):
    def __init__(self,
                 llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"
        ):
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device
        self.MAX_NEW_TOKENS = max_new_tokens

        self.log_mode = log_mode

        self.config = self.load_config(llm_name)
        self.context_manager = SimpleContextManager()
        self.open_sourced = self.config["open_sourced"]
        self.model_type = self.config["model_type"]
        self.model_name = self.config["model_name"]

        self.load_llm_and_tokenizer()
        self.logger = self.setup_logger()

        self.logger.log(
            "AIOS LLM successfully loaded.\n",
            level = "info"
        )

    def convert_map(self, map: dict) -> dict:
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def load_config(self, llm_name):
        # print(os.getcwd())
        config_file = os.path.join(os.getcwd(), "src", "llm_kernel", "llm_config/{}.json".format(llm_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def setup_logger(self):
        logger = LLMKernelLogger(self.model_name)
        return logger

    @abstractmethod
    def load_llm_and_tokenizer(self) -> None: # load model from config
        # raise NotImplementedError
        return

    def address_request(self,
            agent_process,
            temperature=0.0
        ):
        self.process(agent_process)
        return

    @abstractmethod
    def process(self,
                agent_process,
                temperature=0.0) -> None:
        raise NotImplementedError
