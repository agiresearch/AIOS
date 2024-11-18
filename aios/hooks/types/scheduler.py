from pydantic import BaseModel
from typing import Any, TypeAlias, Callable

from .llm import LLMRequestQueueGetMessage
from .memory import MemoryRequestQueueGetMessage
from .storage import StorageRequestQueueGetMessage
from .tool import ToolRequestQueueGetMessage

class SchedulerParams(BaseModel):
    llm: Any
    memory_manager: Any
    storage_manager: Any
    tool_manager: Any
    log_mode: str
    get_llm_syscall: LLMRequestQueueGetMessage | None
    get_memory_syscall: MemoryRequestQueueGetMessage | None
    get_storage_syscall: StorageRequestQueueGetMessage | None
    get_tool_syscall: ToolRequestQueueGetMessage | None