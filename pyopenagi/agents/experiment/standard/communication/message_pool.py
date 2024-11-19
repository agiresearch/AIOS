import threading
import queue
from typing import Any

from pyopenagi.agents.experiment.standard.communication.communication import Communication

SHARED_DICT: dict[Any, queue] = {}


class MessagePool(Communication):
    _pool: dict[Any, queue] = SHARED_DICT

    def __init__(self):
        super().__init__()
        self._lock = threading.Lock()

    async def send(self, message, target):
        with self._lock:
            if target not in self._pool:
                self._pool[target] = queue.Queue()
            self._pool[target].put(message)

    async def receive(self, target):
        pass
