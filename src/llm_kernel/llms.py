from .llm_classes.model_registry import MODEL_REGISTRY
from .llm_classes.open_llm import OpenLLM

class LLMKernel:
    def __init__(self,
                 llm_name: str,
                 max_gpu_memory: dict = None,
                 eval_device: str = None,
                 max_new_tokens: int = 256,
                 log_mode: str = "console"
        ):
        if llm_name in MODEL_REGISTRY.keys():
            # print(llm_name)
            self.model = MODEL_REGISTRY[llm_name](llm_name)
        else:
            self.model = OpenLLM(llm_name=llm_name,
                                 max_gpu_memory=max_gpu_memory,
                                 eval_device=eval_device,
                                 max_new_tokens=max_new_tokens,
                                 log_mode=log_mode)

    def address_request(self,
                        agent_process,
                        temperature=0.0):
        self.model.address_request(agent_process,temperature)
