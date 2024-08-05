from pydantic import BaseModel
from typing import TypeAlias

from aios.llm_core.llms import LLM
from queue import Queue

LLMRequestQueue: TypeAlias = Queue

class LLMParams(BaseModel):
    llm_name: str
    max_gpu_memory: dict | None = None,
    eval_device: str | None = None,
    max_new_tokens: int = 256,
    log_mode: str = "console",
    use_backend: str | None = None


class SchedulerParams(BaseModel):
    llm: LLM
    log_mode: str
    queue: LLMRequestQueue
