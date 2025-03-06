from .base import BaseMemoryManager


class MemoryManager:
    """
    Memory manager for the AIOS system.
    
    This class serves as a high-level interface to the memory management system,
    delegating operations to the BaseMemoryManager implementation. It provides
    a simplified API for agent interaction with the memory subsystem.
    
    Attributes:
        memory_manager (BaseMemoryManager): The underlying memory management implementation
    """
    def __init__(
        self,
        log_mode: str = "console",
    ):
        """
        Initialize the MemoryManager.
        
        Args:
            log_mode (str, optional): Logging mode for memory operations. Defaults to "console".
        """
        self.memory_manager = BaseMemoryManager(
            log_mode=log_mode
        )
        
    def address_request(
        self,
        agent_request,
    ) -> None:
        """
        Process an agent's memory request.
        
        This method delegates the memory operation to the underlying BaseMemoryManager.
        
        Args:
            agent_request: Memory request object from an agent
            
        Returns:
            Result of the memory operation (varies by operation type)
        """
        return self.memory_manager.address_request(agent_request)
