import queue

class BaseQueue:
    def __init__(self):
        self._queue = queue.Queue()

    def add_message(self, message):
        self._queue.put(message)

    def get_message(self, timeout=None):
        try:
            return self._queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def is_empty(self):
        return self._queue.empty()

    def size(self):
        return self._queue.qsize()

    def clear(self):
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break