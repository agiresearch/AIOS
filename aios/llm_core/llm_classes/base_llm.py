# This file contains the abstract base class for each llm kernel, providing a
# common interface for all LLMs to implement.

import json
import re
from aios.context.simple_context import SimpleContextManager

# abc allows to make abstract classes
from abc import ABC, abstractmethod

from aios.utils.logger import LLMKernelLogger

class BaseLLM(ABC):
    def __init__(self,
                 llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"
        ):
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device
        self.max_new_tokens = max_new_tokens

        self.log_mode = log_mode

        self.model_name = llm_name
        self.context_manager = SimpleContextManager()

        self.load_llm_and_tokenizer()
        self.logger = self.setup_logger()

        self.logger.log(
            "AIOS LLM successfully loaded.\n",
            level = "info"
        )

    def convert_map(self, map: dict) -> dict:
        """ helper utility to convert the keys of a map to int """
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def check_model_type(self, model_name):
        # TODO add more model types
        return "causal_lm"

    def setup_logger(self):
        logger = LLMKernelLogger(self.model_name, self.log_mode)
        return logger

    @abstractmethod
    def load_llm_and_tokenizer(self) -> None: # load model from config
        # raise NotImplementedError
        """Load model and tokenizers for each type of LLMs
        """
        return

    # only use for open-sourced LLM
    def tool_calling_input_format(self, messages: list, tools: list) -> list:
        """Integrate tool information into the messages for open-sourced LLMs

        Args:
            messages (list): messages with different roles
            tools (list): tool information
        """
        prefix_prompt = "In and only in current step, you need to call tools. Available tools are: "
        tool_prompt = json.dumps(tools)
        suffix_prompt = "".join(
            [
                'Must call functions that are available. To call a function, respond '
                'immediately and only with a list of JSON object of the following format:'
                '{[{"name":"function_name_value","parameters":{"parameter_name1":"parameter_value1",'
                '"parameter_name2":"parameter_value2"}}]}'
            ]
        )
        messages[-1]["content"] += (prefix_prompt + tool_prompt + suffix_prompt)
        return messages

    def parse_json_format(self, message: str) -> str:
        json_array_pattern = r'\[\s*\{.*?\}\s*\]'
        json_object_pattern = r'\{\s*.*?\s*\}'

        match_array = re.search(json_array_pattern, message)

        if match_array:
            json_array_substring = match_array.group(0)

            try:
                json_array_data = json.loads(json_array_substring)
                return json.dumps(json_array_data)
            except json.JSONDecodeError:
                pass

        match_object = re.search(json_object_pattern, message)

        if match_object:
            json_object_substring = match_object.group(0)

            try:
                json_object_data = json.loads(json_object_substring)
                return json.dumps(json_object_data)
            except json.JSONDecodeError:
                pass
        return '[]'

    def parse_tool_calls(self, message):
        return json.loads(self.parse_json_format(message))

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
