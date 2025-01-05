from enum import Enum

class RouterStrategy(Enum):
    SIMPLE = 0,

class SimpleStrategy:
    def __init__(self, llm_name):
        self.endpoints = llm_name
        self.idx = 0

    def __call__(self):
        return self.get()

    def get(self):
        current  = self.endpoints[self.idx]
        self.idx = (self.idx + 1) % len(self.endpoints)
        return current
