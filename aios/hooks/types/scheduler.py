from pydantic import BaseModel
from typing import Any, TypeAlias, Callable

from .llm import LLMRequestQueueGetMessage
from .memory import MemoryRequestQueueGetMessage

class SchedulerParams(BaseModel):
    llm: Any
    log_mode: str
    get_llm_request: LLMRequestQueueGetMessage | None
    get_memory_request: MemoryRequestQueueGetMessage | None