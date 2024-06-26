# This file contains the abstract base class for each llm kernel, providing a
# common interface for all LLMs to implement.

import os
import json
import re
from aios.context.simple_context import SimpleContextManager

# abc allows to make abstract classes
from abc import ABC, abstractmethod

from aios.utils.logger import LLMKernelLogger

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
        """ helper utility to convert the keys of a map to int """
        new_map = {}
        for k,v in map.items():
            new_map[int(k)] = v
        return new_map

    def load_config(self, llm_name):
        config_file = os.path.join(os.getcwd(), "aios", "llm_kernel", "llm_config/{}.json".format(llm_name))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def check_opensourced(self, model_name):
        """ check against the names as a temporary solution """
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

    # only use for open-sourced LLM
    def tool_calling_input_format(self, messages, tools):
        prefix_prompt = "In and only in current step, you need to call tools. Available tools are: "
        tool_prompt = json.dumps(tools)
        suffix_prompt = "".join(
            [
                'Must call functions that are available. To call a function, respond '
                'immediately and only with a list of JSON object of the following format:'
                '{[{"name":"function_name_value","arguments":{"":"argument_value1",'
                '"argument_name2":"argument_value2"}}]}'
            ]
        )
        messages[-1]["content"] += (prefix_prompt + tool_prompt + suffix_prompt)
        return messages

    def tool_calling_output_format(self, tool_calling_messages):
        # print(f"tool calling messages are: {tool_calling_messages}")
        try:
            tool_callings = []
            tool_calling_messages = json.loads(tool_calling_messages)
            class ToolFunction:
                def __init__(self, name, arguments) -> None:
                    self.name = name
                    self.arguments = arguments

            class ToolCalling:
                def __init__(self, function) -> None:
                    self.function = function

            for tool_calling_message in tool_calling_messages:
                tool_callings.append(
                    ToolCalling(
                        function = ToolFunction(
                            name = tool_calling_message["name"],
                            arguments = json.dumps(tool_calling_message["arguments"])
                        )
                    )
                )
            return tool_callings

        except json.JSONDecodeError:
            return None

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
        raise NotImplementedError

    @abstractmethod
    def process(self,
                agent_process,
                temperature=0.0) -> None:
        raise NotImplementedError
