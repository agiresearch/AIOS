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
    """
    The SimpleStrategy class implements a round-robin selection strategy for load-balancing LLM requests. 
    It iterates through a list of selected language models and returns their corresponding index based on 
    the request count.

    This strategy ensures that multiple models are utilized in sequence, distributing queries evenly across the available configurations.

    Args:
        llm_configs (List[Dict[str, Any]]): A list of LLM configurations, where each dictionary contains model information such as name, backend, and other optional parameters.

    Example:
        ```python
        configs = [
            {"name": "gpt-4o-mini", "backend": "openai"},
            {"name": "qwen2.5-7b", "backend": "ollama"}
        ]

        selected_llms = [
            {"name": "gpt-4o-mini"},
            {"name": "qwen2.5-7b"}
        ]

        strategy = SimpleStrategy(llm_configs=configs)
        model_idxs = strategy.get_model_idxs(selected_llms, n_queries=3)
        ```
    """
    def __init__(self, llm_configs: List[Dict[str, Any]]):
        self.llm_configs = llm_configs
        self.idx = 0 # internal index to track the current model in the round-robin selection.

    # def __call__(self):
    #     return self.get_model()

    def get_model_idxs(self, selected_llms: List[str], n_queries: int=1):
        """
        Selects model indices from the available LLM configurations using a round-robin strategy.

        Args:
            selected_llms (List[str]): A list of selected LLM names from which models will be chosen.
            n_queries (int): The number of queries to distribute among the selected models. Defaults to 1.

        Returns:
            List[int]: A list of indices corresponding to the selected models in `self.llm_configs`.

        """
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
