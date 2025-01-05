from transformers import AutoTokenizer, AutoModelForCausalLM

import os

import vllm

class HfLocalBackend:
    def __init__(self, model_name, device="auto", max_gpu_memory=None):
        self.device = device
        self.max_gpu_memory = max_gpu_memory
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map=device,
            max_memory=self.max_gpu_memory,
            use_auth_token=os.environ["HUGGING_FACE_API_KEY"],
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            use_auth_token=os.environ["HUGGING_FACE_API_KEY"]
        )

    def __call__(
        self,
        messages,
        temperature,
        stream=False,
    ):
        if stream:
            raise NotImplemented

        return ""

class VLLMLocalBackend:
    def __init__(self, model_name, device="auto", max_gpu_memory=None):
        self.device = device
        self.max_gpu_memory = max_gpu_memory

        try:
            import vllm

            self.model = vllm.LLM(
                model_name,
                tensor_parallel_size=1 if max_gpu_memory is None else len(max_gpu_memory)
            )
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        except ImportError:
            raise ImportError("Could not import vllm Python package"
                              "Please install it with `pip install python`")
        except Exception as err:
            print("Error loading vllm model:", err)

    def __call__(
        self,
        messages,
        temperature,
        stream=False,
    ):
        assert vllm
        if stream:
            raise NotImplemented

        parameters = vllm.SamplingParams(temperature=temperature)
        prompt     = self.tokenizer.apply_chat_template(messages,
                                                        tokenize=False)
        response   = self.model.generate(prompt, parameters)
        result     = response[0].outputs[0].text

        return result
