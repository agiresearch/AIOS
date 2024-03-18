from src.memory.base import BaseMemory

class SingleMemory(BaseMemory):
    def __init__(self):
        self.memory_pool = {}

    def mem_save(self, agent_id, content):
        self.memory_pool[agent_id].append(content)

    def mem_load(self, agent_id):
        return self.memory_pool[agent_id]
    
    def mem_alloc(self, agent_id):
        return NotImplementedError
    
    def mem_clear(self, agent_id):
        self.memory_pool[agent_id] = []
