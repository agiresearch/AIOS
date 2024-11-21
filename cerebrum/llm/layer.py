from dataclasses import dataclass

@dataclass
class LLMLayer:
    llm_name: str
    max_gpu_memory: dict | None = None
    eval_device: str = "cuda:0"
    max_new_tokens: int = 2048
    log_mode: str = "console"
    use_backend: str = "default"