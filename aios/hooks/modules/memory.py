from typing import Tuple

from aios.hooks.types.memory import (
    MemoryRequestQueue,
    MemoryRequestQueueGetMessage,
    MemoryRequestQueueAddMessage,
    MemoryRequestQueueCheckEmpty
)
from aios.hooks.utils.validate import validate
from aios.hooks.stores import queue as QueueStore

from aios.hooks.types.memory import MemoryManagerParams

from aios.memory.manager import MemoryManager

def useMemoryRequestQueue() -> (
    Tuple[MemoryRequestQueue, MemoryRequestQueueGetMessage, MemoryRequestQueueAddMessage, MemoryRequestQueueCheckEmpty]
):
    """
    Creates and returns a queue for Memory-related requests along with helper methods to manage the queue.

    Returns:
        Tuple: A tuple containing the Memory request queue, get message function, add message function, and check queue empty function.
    """
    # r_str = (
    #     generate_random_string()
    # )  # Generate a random string for queue identification
    r_str = "memory"
    _ = MemoryRequestQueue()

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

@validate(MemoryManagerParams)
def useMemoryManager(params):
    """
    Initialize and return a memory instance.

    Args:
        params (MemoryParams): Parameters required for Memory Manager Initialization.

    Returns:
        Memory Manager: An instance of the initialized Memory Manager.
    """
    return MemoryManager(**params.model_dump())