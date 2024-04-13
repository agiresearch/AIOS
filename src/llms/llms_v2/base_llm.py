from openai import OpenAI
import os
import json
import re
import time
from datetime import datetime
from src.context.simple_context import SimpleContextManager
import logging
from abc import ABC, abstractmethod


class BaseLLMKernel(ABC):
    def __init__(self,
                 llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"
        ):
        print("Initialize AIOS powered by LLM: {}".format(llm_name))
        self.config = self.load_config(llm_name)
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device

        self.log_mode = log_mode

        self.load_llm_and_tokenizer()
        self.MAX_NEW_TOKENS = max_new_tokens
        self.logger = self.setup_logger()
        self.context_manager = SimpleContextManager()
        self.open_sourced = self.config["open_sourced"]
        self.model_type = self.config["model_type"]
        self.model_name = self.config["model_name"]
        print("AIOS LLM successfully loaded. ")
        self.model = None
        self.tokenizer = None

    def convert_map(self, map: dict) -> dict:
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def load_config(self, llm_name):
        # print(os.getcwd())
        config_file = os.path.join(os.getcwd(), "src", "llms", "../llm_config/{}.json".format(llm_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def setup_logger(self):
        logger = logging.getLogger(f"FIFO Scheduler Logger")
        # logger.setLevel(logging.INFO)  # Set the minimum logging level
        date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Provide two log modes: console and file
        # Ensure the logger doesn't propagate to the root logger
        logger.propagate = False

        # Remove all handlers associated with this logger
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

        if self.log_mode == "console":
            handler = logging.StreamHandler()
            handler.setLevel(logging.INFO)  # Set logging level for console output
        else:
            assert self.log_mode == "file"
            log_dir = os.path.join(os.getcwd(), "logs", "scheduler")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            log_file = os.path.join(log_dir, f"{date_time}.txt")
            handler = logging.FileHandler(log_file)
            handler.setLevel(logging.INFO)  # Set logging

        logger.addHandler(handler) # enabled when run in a simulated shell
        return logger

    @abstractmethod
    def load_llm_and_tokenizer(self) -> None: # load model from config
        raise NotImplementedError

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

