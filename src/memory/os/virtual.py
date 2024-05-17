import tiktoken
from src.memory.os.meta import Message

class VirtualMemory:
    def __init__(self, system: str | None = None, max_buffer=6000):
        self.memory: list[Message] = []
        self.max_buffer = max_buffer

    def _num_tokens(self, string: str) -> int:
        encoding = tiktoken.get_encoding("cl100k_base")
        num_tokens = len(encoding.encode(string))
        return num_tokens

    def _check_buffer(self):
        buffer_length = self._num_tokens(
            ' '.join([msg.content for msg in self.memory])
        )

        return buffer_length <= self.max_buffer
    
    def clip_memory(self, order=0):
        if order >= 0:
            dislocated = self.memory.pop(order)
        else:
            dislocated = self.memory.pop(len(self.memory) + order)
        
        if dislocated.role == 'user':
            if order >= 0:
                dislocated_aux = self.memory.pop(order)
            else:
                dislocated_aux = self.memory.pop(len(self.memory) + order)
        else:
            dislocated_aux = None

        return (dislocated, dislocated_aux)
        
    def add_memory(self, role, content):
        self.memory.append(
            Message(content=content, role=role)
        )

    def read_memory(self):
        builder = ''

        for msg in self.memory:
            builder += f'{msg.role}: {msg.content} \n'
        
        return builder