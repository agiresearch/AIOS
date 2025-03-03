from pydantic import BaseModel
from typing import Any, TypeAlias, Callable, List, Dict
from queue import Queue

LLMRequestQueue: TypeAlias = Queue
# LLMRequestQueue: TypeAlias = []

LLMRequestQueueGetMessage: TypeAlias = Callable[[], None]
LLMRequestQueueAddMessage: TypeAlias = Callable[[str], None]
LLMRequestQueueCheckEmpty: TypeAlias = Callable[[], bool]


class LLMParams(BaseModel):
    llm_configs: List[Dict[str, Any]]
    log_mode: str = ("console",)
    use_context_manager: bool = False
