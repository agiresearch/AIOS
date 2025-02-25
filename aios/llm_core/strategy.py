from enum import Enum

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
    def __init__(self, llm_name: list[str]):
        self.endpoints = llm_name
        self.idx = 0

    def __call__(self):
        return self.get()

    def get(self):
        current  = self.endpoints[self.idx]
        self.idx = (self.idx + 1) % len(self.endpoints)
        return current
