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

        self.model_name = llm_name
        self.context_manager = SimpleContextManager()
        self.open_sourced = self.check_opensourced(self.model_name)
        self.model_type = self.check_model_type(self.model_name)

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
        config_file = os.path.join(os.getcwd(), "src", "llm_kernel", "llm_config/{}.json".format(llm_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def check_opensourced(self, model_name):
        pattern = r'(?i)\bgpt\b|\bclaude\b|\bgemini\b'
        return re.search(pattern, model_name) is not None

    def check_model_type(self, model_name):
        # TODO add more model types
        return "causal_lm"

    def setup_logger(self):
        logger = LLMKernelLogger(self.model_name, self.log_mode)
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

    def address_request_list(self,
            agent_process,
            temperature=0.0
        ):
        steps = agent_process.prompt.split(";")
        for step in steps:
            self.process
        return

    @abstractmethod
    def process(self,
                agent_process,
                temperature=0.0) -> None:
        raise NotImplementedError
