from src.memory.base import BaseMemory

class SingleMemory(BaseMemory):
    def __init__(self):
        self.memory_pool = []

    def save_memory(self, content):
        self.memory_pool.append(content)

    def load(self):
        return self.memory_pool
