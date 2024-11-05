from pydantic import BaseModel
from typing import Any, TypeAlias, Callable
from queue import Queue

MemoryRequestQueue: TypeAlias = Queue

MemoryRequestQueueGetMessage: TypeAlias = Callable[[], None]
MemoryRequestQueueAddMessage: TypeAlias = Callable[[str], None]
MemoryRequestQueueCheckEmpty: TypeAlias = Callable[[], bool]

class MemoryManagerParams(BaseModel):
    memory_limit: int
    eviction_k: int
    storage_manager: Any