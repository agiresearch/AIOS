from random import randint

from typing import Tuple

from aios.tool.base import ToolManager
from aios.hooks.types.tool import (
    ToolRequestQueue,
    ToolRequestQueueAddMessage,
    ToolRequestQueueCheckEmpty,
    ToolRequestQueueGetMessage
)
from aios.hooks.utils.validate import validate
from aios.hooks.stores import queue as QueueStore, processes as ProcessStore

# @validate(ToolManagerParams)
def useToolManager(params) -> ToolManager:
    """
    Initialize and return a tool manager instance.

    Args:
        params (ToolParams): Parameters required for Tool Manager Initialization.

    Returns:
        Tool Manager: An instance of the initialized Tool Manager.
    """
    return ToolManager(**params.model_dump())

def useToolRequestQueue() -> (
    Tuple[ToolRequestQueue, ToolRequestQueueGetMessage, ToolRequestQueueAddMessage, ToolRequestQueueCheckEmpty]
):
    """
    Creates and returns a queue for Storage-related requests along with helper methods to manage the queue.

    Returns:
        Tuple: A tuple containing the Memory request queue, get message function, add message function, and check queue empty function.
    """
    # r_str = (
    #     generate_random_string()
    # )  # Generate a random string for queue identification
    r_str = "tool"
    _ = ToolRequestQueue()

    # Store the LLM request queue in QueueStore
    QueueStore.REQUEST_QUEUE[r_str] = _

    # Function to get messages from the queue
    def getMessage():
        return QueueStore.getMessage(_)

    # Function to add messages to the queue
    def addMessage(message: str):
        return QueueStore.addMessage(_, message)

    # Function to check if the queue is empty
    def isEmpty():
        return QueueStore.isEmpty(_)

    return _, getMessage, addMessage, isEmpty

# @validate(MemoryManagerParams)
# def useMemoryManager(params: MemoryManagerParams) -> MemoryManager:
#     """
#     Initialize and return a memory instance.

#     Args:
#         params (MemoryParams): Parameters required for Memory Manager Initialization.

#     Returns:
#         Memory Manager: An instance of the initialized Memory Manager.
#     """
#     return MemoryManager(**params.model_dump())