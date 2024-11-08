from queue import Queue

REQUEST_QUEUE: dict[str, Queue] = {}

def getMessage(q: Queue):
    return q.get(block=True, timeout=0.1)

def addMessage(q: Queue, message: str):
    q.put(message)

    return None

def isEmpty(q: Queue):
    return q.empty()
