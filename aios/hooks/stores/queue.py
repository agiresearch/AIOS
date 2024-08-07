from aios.hooks.types.llm import LLMRequestQueue

LLM_REQUEST_QUEUE: dict[str, LLMRequestQueue] = {}

def getMessage(q: LLMRequestQueue):
    return q.get(block=True, timeout=1)

def addMessage(q: LLMRequestQueue, message: str):
    q.put(message)

    return None

def isEmpty(q: LLMRequestQueue):
    return q.empty()
