from pydantic import BaseModel
from typing import Any, TypeAlias, Callable

from .llm import LLMRequestQueueGetMessage
from .memory import MemoryRequestQueueGetMessage
from .storage import StorageRequestQueueGetMessage
from .tool import ToolRequestQueueGetMessage

class SchedulerParams(BaseModel):
    llm: Any
    log_mode: str
    get_llm_request: LLMRequestQueueGetMessage | None
    get_memory_request: MemoryRequestQueueGetMessage | None
    get_storage_request: MemoryRequestQueueGetMessage | None
    get_tool_request: MemoryRequestQueueGetMessage | None