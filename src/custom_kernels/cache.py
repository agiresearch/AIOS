from src.memory.os.meta import Message
from copy import deepcopy

class Cache:
    def __init__(self, stop_sequence='$^@'):
        self.trailing = []
        self.leading = []
        self.history: list[Message] = []
        self.stop_sequence = stop_sequence
        self.__gate = False
    
    def add_user(self, phrase=''):
        self.history.append(
            Message(role='user', content=phrase)
        )

    def stream(self, token: str):
        if self.stop_sequence == token:
            self.segment()

        if self.gate():
            self.trailing.append(token)
        else:
            self.leading.append(token)


    def segment(self):
        if len(self.history) == 0  or self.history[-1].role == 'user':
            self.history.append(
                Message(role='assistant', content=''.join(self.leading))
            )
        else:
            self.history[-1].content += '  [PAUSED]  ' + ''.join(self.leading)

        self.leading = deepcopy(self.trailing)
        self.trailing = []


    def toggle(self):
        self.__gate = not self.__gate

    def gate(self):
        return self.__gate

    def clear(self, sets=['trailing, leading']):
        if 'leading' in sets:
            self.leading = []
        if 'trailing' in sets:
            self.trailing = []
