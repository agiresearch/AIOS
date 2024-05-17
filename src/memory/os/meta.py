
from typing import Union

class Message:
    def __init__(self, role: Union["assistant", "user"], content: str): 
        self.role = role
        self.content = content