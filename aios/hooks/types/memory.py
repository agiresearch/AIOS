from pydantic import BaseModel
from typing import Any, TypeAlias, Callable, Optional
from queue import Queue

MemoryRequestQueue: TypeAlias = Queue
# MemoryRequestQueue: TypeAlias = []

MemoryRequestQueueGetMessage: TypeAlias = Callable[[], None]
MemoryRequestQueueAddMessage: TypeAlias = Callable[[str], None]
MemoryRequestQueueCheckEmpty: TypeAlias = Callable[[], bool]

class MemoryManagerParams(BaseModel):
    log_mode: str
    provider: Optional[str] = "in-house"  # Memory provider type: "in-house", "mem0", or "zep"