class SessionMemory:
    def __init__(self):
        self.memory = []

    def add_memory(self, chunk):
        self.memory.append(chunk)

    def read_memory(self):
        return ' '.join(self.memory)