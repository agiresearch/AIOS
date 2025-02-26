from pydantic import BaseModel
from typing import Any, TypeAlias, Callable
from queue import Queue

ToolRequestQueue: TypeAlias = Queue
# ToolRequestQueue: TypeAlias = []

ToolRequestQueueGetMessage: TypeAlias = Callable[[], None]
ToolRequestQueueAddMessage: TypeAlias = Callable[[str], None]
ToolRequestQueueCheckEmpty: TypeAlias = Callable[[], bool]

class ToolManagerParams(BaseModel):
    name: str
    params: dict | None = (None,)