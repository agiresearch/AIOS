from queue import Queue
from typing import List
REQUEST_QUEUE: dict[str, Queue] = {}
# REQUEST_QUEUE: dict[str, []] = {}


def getMessage(q: List):
    return q.get(block=True, timeout=0.1)
    # return q.pop(0)

def addMessage(q: List, message: str):
    # q.append(message)
    q.put(message)
    return None

def isEmpty(q: List):
    # return len(q) == 0
    return q.empty()