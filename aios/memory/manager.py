"""
Memory Manager for the AIOS system.

This module provides the MemoryManager class that serves as the high-level
interface to the memory management system. It uses pluggable memory providers
to enable different storage backends (in-house, Mem0, Zep).
"""
from typing import Optional, Dict, Any

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from aios.config.config_manager import config as global_config
from .providers import ProviderFactory, MemoryProvider


class MemoryManager:
    """
    Memory manager using pluggable providers.
    
    This class serves as a high-level interface to the memory management system,
    delegating operations to a configured memory provider. It supports multiple
    backend providers (in-house, Mem0, Zep) through the provider abstraction layer.
    
    The manager maintains backward compatibility with existing code by defaulting
    to the "in-house" provider when no provider is specified.
    
    Attributes:
        provider (MemoryProvider): The configured memory provider instance
    """
    
    def __init__(
        self,
        log_mode: str = "console",
        provider: Optional[str] = None,
    ):
        """
        Initialize the MemoryManager.
        
        Args:
            log_mode: Logging mode for memory operations. Defaults to "console".
            provider: Optional provider type to use. If not specified, uses the
                     provider from configuration or defaults to "in-house".
                     Valid values: "in-house", "mem0", "zep"
        """
        self.log_mode = log_mode
        
        # Get configuration
        memory_config = global_config.get_memory_config() or {}
        storage_config = global_config.get_storage_config() or {}
        
        # Determine provider type: explicit parameter > config > default
        provider_type = provider or memory_config.get("provider", "in-house")
        
        # Get provider-specific configuration
        provider_config = self._get_provider_config(
            provider_type, memory_config, storage_config
        )
        
        # Create the provider using the factory
        self.provider = ProviderFactory.create(provider_type, provider_config)
    
    def _get_provider_config(
        self,
        provider_type: str,
        memory_config: Dict[str, Any],
        storage_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get provider-specific configuration.
        
        Extracts the appropriate configuration section based on the provider type.
        
        Args:
            provider_type: The type of provider ("in-house", "mem0", "zep")
            memory_config: The memory configuration section from config
            storage_config: The storage configuration section from config
        
        Returns:
            Dictionary containing provider-specific configuration
        """
        if provider_type == "in-house":
            return storage_config
        elif provider_type == "mem0":
            return memory_config.get("mem0", {})
        elif provider_type == "zep":
            return memory_config.get("zep", {})
        return {}
    
    def _analyze_query_to_memory(self, query: MemoryQuery) -> 'MemoryNote':
        """
        Convert a MemoryQuery to a MemoryNote object.
        
        This method extracts parameters from a MemoryQuery and creates a
        MemoryNote object suitable for provider operations.
        
        Args:
            query: Memory query containing parameters
        
        Returns:
            MemoryNote created from query parameters
        """
        from .note import MemoryNote
        
        params = query.params
        valid_keys = [
            "content", "id", "keywords", "links", "retrieval_count",
            "timestamp", "last_accessed", "context", "evolution_history",
            "category", "tags"
        ]
        
        # Extract metadata if present
        metadata = params.get("metadata", {})
        
        # Create filtered data dictionary
        filtered_data = {}
        
        # Add direct parameters
        for k in params:
            if k in valid_keys:
                filtered_data[k] = params[k]
        
        # Handle memory_id specifically
        if "memory_id" in params and "id" not in filtered_data:
            filtered_data["id"] = params["memory_id"]
        
        # Add metadata fields if they exist
        if "tags" in metadata and "tags" not in filtered_data:
            filtered_data["tags"] = metadata.get("tags", [])
        if "keywords" in metadata and "keywords" not in filtered_data:
            filtered_data["keywords"] = metadata.get("keywords", [])
        if "category" in metadata and "category" not in filtered_data:
            filtered_data["category"] = metadata.get("category", "Uncategorized")
        
        memory_note = MemoryNote(**filtered_data)
        return memory_note
    
    def address_request(self, memory_syscall) -> MemoryResponse:
        """
        Process an agent's memory request.
        
        Routes the memory syscall to the appropriate provider method based
        on the operation type specified in the syscall's query.
        
        Args:
            memory_syscall: Memory syscall object containing the operation
                           and parameters
        
        Returns:
            MemoryResponse containing the result of the operation
        
        Raises:
            TypeError: If memory_syscall is not a MemorySyscall
            ValueError: If the operation type is invalid
        """
        # Import here to avoid circular dependency
        from aios.syscall.memory import MemorySyscall
        
        if not isinstance(memory_syscall, MemorySyscall):
            raise TypeError(f"Expected MemorySyscall, got {type(memory_syscall)}")
        
        query = memory_syscall.query
        operation_type = query.operation_type
        
        if operation_type == "add_memory":
            memory_note = self._analyze_query_to_memory(query)
            return self.provider.add_memory(memory_note)
        
        elif operation_type == "remove_memory":
            return self.provider.remove_memory(query.params["memory_id"])
        
        elif operation_type == "update_memory":
            memory_note = self._analyze_query_to_memory(query)
            return self.provider.update_memory(memory_note)
        
        elif operation_type == "get_memory":
            return self.provider.get_memory(query.params["memory_id"])
        
        elif operation_type == "retrieve_memory":
            return self.provider.retrieve_memory(query)
        
        elif operation_type == "retrieve_memory_raw":
            return self.provider.retrieve_memory_raw(query)
        
        else:
            raise ValueError(f"Invalid operation: {operation_type}")
    
    def close(self) -> None:
        """
        Clean up resources.
        
        Delegates to the provider's close method to release any held resources.
        """
        if self.provider:
            self.provider.close()
