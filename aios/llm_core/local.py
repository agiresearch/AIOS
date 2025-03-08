from transformers import AutoTokenizer, AutoModelForCausalLM
from litellm import completion

from transformers import pipeline

import re

import os

from aios.config.config_manager import config

class HfLocalBackend:
    def __init__(self, model_name, max_gpu_memory=None, eval_device=None, hostname=None):
        print("\n=== HfLocalBackend Initialization ===")
        print(f"Model name: {model_name}")
        print(f"Checking HF API key:")
        print(f"HUGGING_FACE_API_KEY in env: {'Yes' if 'HUGGING_FACE_API_KEY' in os.environ else 'No'}")
        print(f"HF_AUTH_TOKEN in env: {'Yes' if 'HF_AUTH_TOKEN' in os.environ else 'No'}")
        
        self.model_name = model_name
        self.max_gpu_memory = max_gpu_memory
        self.eval_device = eval_device
        self.hostname = hostname

        # If a hostname is given, then this HF instance is hosted as a web server.
        # Therefore, do not start the AIOS-based HF instance.
        if self.hostname is not None:
            return
        
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto",
            max_memory=self.max_gpu_memory,
            use_auth_token=os.environ["HF_TOKEN"],
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            device_map="auto",
            use_auth_token=os.environ["HF_TOKEN"]
        )
        self.tokenizer.chat_template = "{% for message in messages %}{% if message['role'] == 'user' %}{{ ' ' }}{% endif %}{{ message['content'] }}{% if not loop.last %}{{ ' ' }}{% endif %}{% endfor %}{{ eos_token }}"

    def inference_online(self, messages, temperature, stream=False):
        return completion(
            model="huggingface/" + self.model_name,
            messages=messages,
            temperature=temperature,
            api_base=self.hostname,
        ).choices[0].message.content
    
    def __call__(
        self,
        messages,
        temperature,
        stream=False,
    ):
        if self.hostname is not None:
            return self.inference_online(messages, temperature, stream=stream)
        
        if stream:
            raise NotImplemented

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_dict=True,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        temperature = temperature if temperature > 0.5 else 0.5
        response  = self.model.generate(
            **inputs,
            temperature=temperature,
            max_length=4096,
            top_k=10,
            num_beams=4,
            early_stopping=True,
            do_sample=True,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id
        )
        length = inputs["input_ids"].shape[1]
        result = self.tokenizer.decode(response[0][length:]).replace("assistant\n\n", "")

        return result
    
    def generate(self, messages, temperature=1.0, tools=None, max_length=1024):
        # breakpoint()
        if self.hostname is not None:
            return self.inference_online(messages, temperature, stream=stream)

        inputs = self.tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            # add_generation_prompt=True,
            tools=tools,
            return_dict=True,
            return_tensors="pt"
        )
        inputs = {k: v.to(self.eval_device) for k, v in inputs.items()}
        temperature = temperature if temperature > 0.5 else 0.5
        response  = self.model.generate(
            **inputs,
            temperature=temperature,
            max_length=max_length,
            top_k=10,
            num_beams=4,
            early_stopping=True,
            do_sample=True,
            num_return_sequences=1,
            eos_token_id=self.tokenizer.eos_token_id
        )
        length = inputs["input_ids"].shape[1]
        result = self.tokenizer.decode(response[0][length:], skip_special_tokens=True)
        
        breakpoint()
        
        result = re.sub(r'^\s*assistant[：:]?\s*|\<\/?assistant\>|assistant\n\n', '', result, flags=re.IGNORECASE)
        result = result.lstrip()
        
        return result
