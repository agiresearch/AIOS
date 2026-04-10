"""
Abstract base class for memory providers.

This module defines the MemoryProvider interface that all memory provider
implementations must follow. The interface enables pluggable memory backends
while maintaining a consistent API across different storage solutions.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, TYPE_CHECKING

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

if TYPE_CHECKING:
    from aios.memory.note import MemoryNote


class MemoryProvider(ABC):
    """Abstract base class for memory providers.
    
    All memory provider implementations (InHouseProvider, Mem0Provider, 
    ZepProvider) must inherit from this class and implement all abstract methods.
    
    The provider abstraction enables:
    - Pluggable memory backends without changing application code
    - Consistent API across different storage solutions
    - Easy addition of new memory providers
    """
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        This method is called after provider instantiation to configure
        the provider with backend-specific settings.
        
        Args:
            config: Provider-specific configuration dictionary.
                   For InHouseProvider: vector_db_backend, etc.
                   For Mem0Provider: api_key, user_id, llm, embedder, etc.
                   For ZepProvider: api_key, base_url, session_id, etc.
        
        Raises:
            ProviderInitializationError: If initialization fails due to
                invalid configuration or connection issues.
        """
        pass
    
    @abstractmethod
    def add_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Add a memory note to storage.
        
        Args:
            memory_note: The memory note to store, containing content
                        and associated metadata (keywords, tags, category, etc.)
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message on failure.
        """
        pass
    
    @abstractmethod
    def remove_memory(self, memory_id: str) -> MemoryResponse:
        """Remove a memory by ID.
        
        Args:
            memory_id: Unique identifier of the memory to remove.
        
        Returns:
            MemoryResponse with success=True on successful removal,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def update_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Update an existing memory.
        
        Args:
            memory_note: The memory note with updated content/metadata.
                        The memory_note.id identifies which memory to update.
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def get_memory(self, memory_id: str) -> MemoryResponse:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: Unique identifier of the memory to retrieve.
        
        Returns:
            MemoryResponse with success=True, content, and metadata on success,
            or success=False with error message if memory not found.
        """
        pass
    
    @abstractmethod
    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        """Search for memories matching the query.
        
        Performs semantic search to find memories similar to the query content.
        
        Args:
            query: MemoryQuery containing search parameters:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return
        
        Returns:
            MemoryResponse with success=True and search_results containing
            a list of matching memories with their content and metadata.
        """
        pass
    
    @abstractmethod
    def retrieve_memory_raw(self, query: MemoryQuery) -> List['MemoryNote']:
        """Retrieve raw memory objects for internal processing.
        
        Similar to retrieve_memory but returns raw MemoryNote objects
        instead of a formatted MemoryResponse. Used for internal operations
        that need direct access to memory objects.
        
        Args:
            query: MemoryQuery containing search parameters:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return (default: 5)
        
        Returns:
            List of MemoryNote objects matching the query.
        """
        pass
    
    def close(self) -> None:
        """Clean up resources.
        
        Override this method if the provider needs to release resources,
        close connections, or perform cleanup operations when shutting down.
        
        For providers with external connections (Mem0, Zep), this should
        properly disconnect from external services.
        
        The default implementation is a no-op for backward compatibility.
        """
        pass
