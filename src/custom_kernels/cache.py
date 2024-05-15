from src.memory.os.meta import Message
from copy import deepcopy


class Cache:
    def __init__(self, stop_sequence='$^@'):
        self.trailing = []
        self.leading = []
        self.history: list[Message] = []
        self.stop_sequence = stop_sequence
        self.__gate = False
        self.hidden = []

    def add_user(self, phrase=''):
        m = Message(role='user', content=phrase)

        self.history.append(
            m
        )

        return m

    def stream(self, token: str, show_breaks=False):
        if self.stop_sequence == token:
            self.segment(show_breaks=show_breaks)
            return

        if self.gate():
            self.trailing.append(token)
        else:
            self.leading.append(token)

    def segment(self, show_breaks=False):
        if self.gate() == False:
            if len(self.trailing) > 0 and show_breaks:
                self.leading = deepcopy(self.leading + [' [PAUSE] '] + self.trailing )
            else:
                self.leading = deepcopy(self.leading + self.trailing)
            
            self.trailing = []

            if len(self.history) == 0 or self.history[-1].role == 'user':
                m = Message(role='assistant', content=''.join(self.leading))

                self.history.append(
                    m
                )

                return m
            else:
                self.history[-1].content = ''.join(self.leading)

    def toggle(self, hard=None):
        if hard:
            self.__gate = hard
            return 
        self.__gate = not self.__gate

    def gate(self):
        return self.__gate

    def clear(self, sets=['trailing, leading']):
        if 'leading' in sets:
            self.leading = []
        if 'trailing' in sets:
            self.trailing = []
