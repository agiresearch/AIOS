from enum import Enum
from typing import List, Dict, Any
"""
Load balancing strategies. Each class represents a strategy which returns the
next endpoint that the router should use.

Each strategy must implement the following:
    __init__(self, llm_name: list[str])
    __call__(self)

The llm_name list contains all the endpoints that the router was initialized
with. It is the strategy's job to then calculate which endpoint should be
used whenever the strategy is called in __call__, and then return the name of
the specific LLM endpoint.
"""

class RouterStrategy(Enum):
    SIMPLE = 0,

class SimpleStrategy:
    def __init__(self, llm_configs: List[Dict[str, Any]]):
        self.llm_configs = llm_configs
        self.idx = 0

    # def __call__(self):
    #     return self.get_model()

    def get_model_idxs(self, selected_llms: List[str], n_queries: int=1):
        # current  = self.selected_llms[self.idx]
        model_idxs = []
        
        for _ in range(n_queries):
            current = selected_llms[self.idx]
            for i, llm_config in enumerate(self.llm_configs):
                # breakpoint()
                if llm_config["name"] == current["name"]:
                    model_idxs.append(i)
                    break
            self.idx = (self.idx + 1) % len(selected_llms)
        
        return model_idxs
