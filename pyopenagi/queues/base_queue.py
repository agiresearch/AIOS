import queue

class BaseQueue:

    _queue = queue.Queue()

    @classmethod
    def add_message(cls, message):
        cls._queue.put(message)

    @classmethod
    def get_message(cls):
        return cls._queue.get(block=True, timeout=1)

    @classmethod
    def is_empty(cls):
        return cls._queue.empty()
