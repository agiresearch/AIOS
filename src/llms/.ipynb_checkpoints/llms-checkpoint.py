import torch

import sys

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
)

model_class = {
    "causal_lm": AutoModelForCausalLM,
}

from openai import OpenAI

# sys.path.append("..")

import os

import json

class LLMKernel:
    def __init__(self, kernel_type):
        print("Initialize Jarvos kernel powered by: {}".format(kernel_type))
        self.config = self.load_config(kernel_type)
        self.llm = self.load_llm()
        print("AIOS LLM successfully loaded. ")


    def load_config(self, kernel_type):
        # print(os.getcwd())
        config_file = os.path.join(os.getcwd(), "src", "llms", "llm_config/{}.json".format(kernel_type))
        with open(config_file, "r") as f:
            config = json.load(f)
            return config

    def load_llm(self): # load model from config
        open_sourced = self.config["open_sourced"]
        model_type = self.config["model_type"]
        model_name = self.config["model_name"]
        self.llm_name = model_name
        
        if open_sourced:
            hf_token = self.config["hf_token"] if "hf_token" in self.config.keys() else None
            cache_dir = self.config["cache_dir"] if "cache_dir" in self.config.keys() else None
            model = model_class[model_type].from_pretrained(
                model_name,
                use_auth_token = hf_token,
                cache_dir = cache_dir
            )
        else:
            if model_name_or_path == "gpt3.5-turbo":
                model = OpenAI()
                return model
            else:
                return NotImplementedError
        return model
