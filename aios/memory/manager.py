from .base import BaseMemoryManager


class MemoryManager:
    """
    Memory manager for the AIOS system.
    """
    def __init__(
        self,
        log_mode: str = "console",
    ):
        self.memory_manager = BaseMemoryManager(
            log_mode=log_mode
        )
        
    def address_request(
        self,
        agent_request,
    ) -> None:
        return self.memory_manager.address_request(agent_request)
