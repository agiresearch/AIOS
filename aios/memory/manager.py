from .memory_classes.single_memory import SingleMemoryManager


class MemoryManager:
    def __init__(
        self,
        memory_limit,
        eviction_k,
        storage_manager,
        log_mode: str = "console",
    ):
        self.memory_manager = SingleMemoryManager(
            memory_limit,
            eviction_k,
            storage_manager
        )

    def address_request(
        self,
        agent_request,
    ) -> None:
        return self.memory_manager.address_request(agent_request)
