from typing import Any, Tuple, Callable, Dict
from random import randint

from aios.llm_core.llms import LLM
from aios.hooks.types.scheduler import (
    # AgentSubmitDeclaration,
    # FactoryParams,
    # LLMParams,
    SchedulerParams,
    # LLMRequestQueue,
    # QueueGetMessage,
    # QueueAddMessage,
    # QueueCheckEmpty,
)

from contextlib import contextmanager

from aios.hooks.utils.validate import validate
from aios.hooks.stores import queue as QueueStore, processes as ProcessStore
from aios.scheduler.fifo_scheduler import FIFOScheduler


@validate(SchedulerParams)
def useFIFOScheduler(
    params: SchedulerParams,
) -> Tuple[Callable[[], None], Callable[[], None]]:
    """
    Initialize and return a scheduler with start and stop functions.

    Args:
        params (SchedulerParams): Parameters required for the scheduler.

    Returns:
        Tuple: A tuple containing the start and stop functions for the scheduler.
    """
    if params.get_llm_request is None:
        from aios.hooks.stores._global import global_llm_req_queue_get_message
        params.get_llm_request = global_llm_req_queue_get_message
        
    if params.get_memory_request is None:
        from aios.hooks.stores._global import global_memory_req_queue_get_message
        params.get_memory_request = global_memory_req_queue_get_message
        
    if params.get_storage_request is None:
        from aios.hooks.stores._global import global_storage_req_queue_get_message
        params.get_storage_request = global_storage_req_queue_get_message
        
    if params.get_tool_request is None:
        from aios.hooks.stores._global import global_tool_req_queue_get_message
        params.get_tool_request = global_tool_req_queue_get_message

    scheduler = FIFOScheduler(**params.model_dump())

    # Function to start the scheduler
    def startScheduler():
        scheduler.start()

    # Function to stop the scheduler
    def stopScheduler():
        scheduler.stop()

    return startScheduler, stopScheduler


@contextmanager
@validate(SchedulerParams)
def fifo_scheduler(params: SchedulerParams):
    """
    A context manager that starts and stops a FIFO scheduler.

    Args:
        params (SchedulerParams): The parameters for the scheduler.
    """
    if params.get_llm_request is None:
        from aios.hooks.stores._global import global_llm_req_queue_get_message
        params.get_llm_request = global_llm_req_queue_get_message

    if params.get_memory_request is None:
        from aios.hooks.stores._global import global_memory_req_queue_get_message
        params.get_memory_request = global_memory_req_queue_get_message
    
    if params.get_storage_request is None:
        from aios.hooks.stores._global import global_storage_req_queue_get_message
        params.get_storage_request = global_storage_req_queue_get_message
        
    if params.get_tool_request is None:
        from aios.hooks.stores._global import global_tool_req_queue_get_message
        params.get_tool_request = global_tool_req_queue_get_message
    
    scheduler = FIFOScheduler(**params.model_dump())

    scheduler.start()
    yield
    scheduler.stop()
