from pydantic import BaseModel
from typing import Any, TypeAlias, Callable

from queue import Queue

from pyopenagi.agents.agent_process import AgentProcess

LLMRequestQueue: TypeAlias = Queue[AgentProcess]

QueueGetMessage: TypeAlias = Callable[[], AgentProcess]
QueueAddMessage: TypeAlias = Callable[[str], None]
QueueCheckEmpty: TypeAlias = Callable[[], bool]

class LLMParams(BaseModel):
    llm_name: str
    max_gpu_memory: dict | None = None,
    eval_device: str | None = None,
    max_new_tokens: int = 256,
    log_mode: str = "console",
    use_backend: str | None = None


class SchedulerParams(BaseModel):
    llm: Any
    log_mode: str
    get_queue_message: QueueGetMessage | None


class FactoryParams(BaseModel):
    log_mode: str = "console",
    max_workers: int = 500

class AgentSubmitDeclaration(BaseModel):
    agent_name: str
    task_input: str | int | float | dict | tuple | list
