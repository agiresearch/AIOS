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

    async def send(self, message: Any, target: Any) -> None:
        with self._lock:
            if target not in self._pool:
                self._pool[target] = queue.Queue()
            self._pool[target].put(message)

    async def receive(self, target: Any) -> Any:
        if target not in self._pool:
            yield None

        with self._lock:
            if target in self._pool:
                queue = self._pool[target]
                while not queue.empty():
                    yield queue.get()
