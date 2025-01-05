from transformers import AutoTokenizer, AutoModelForCausalLM

class HfLocalBackend:
    def __init__(self, device = "cuda:0"):
        pass

    def __call__(
        self,
        messages,
        temperature,
    ):
        return ""

class VLLMLocalBackend:
    def __call__(
        self,
        messages,
        temperature,
    ):
        return ""
