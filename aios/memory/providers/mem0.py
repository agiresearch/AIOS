"""
Mem0Provider - Memory provider using Mem0 for AI-native memory management.

This provider integrates with the Mem0 library to provide AI-native memory
management capabilities including automatic memory extraction, semantic search,
and intelligent memory organization.
"""
from typing import Dict, Any, List, TYPE_CHECKING

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from .base import MemoryProvider

if TYPE_CHECKING:
    from aios.memory.note import MemoryNote


class Mem0Provider(MemoryProvider):
    """Provider using Mem0 for memory management.
    
    Mem0 provides AI-native memory management with features like:
    - Automatic memory extraction from conversations
    - Semantic search across memories
    - User and agent-scoped memory organization
    
    Attributes:
        client: Mem0 Memory client instance
        default_user_id: Default user ID for memory operations
        default_agent_id: Default agent ID for memory operations
    """
    
    def __init__(self):
        """Initialize the Mem0Provider with empty state.
        
        The actual Mem0 client is created during initialize() based on config.
        """
        self.client = None
        self.default_user_id = "default"
        self.default_agent_id = None
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with Mem0 configuration.
        
        Creates and configures the Mem0 Memory client with the provided
        settings for LLM, embedder, and vector store.
        
        Args:
            config: Configuration dictionary containing:
                   - user_id: Default user ID (default: "default")
                   - agent_id: Default agent ID (optional)
                   - llm: LLM configuration dict
                   - embedder: Embedder configuration dict
                   - vector_store: Vector store configuration dict
                   - api_key: Mem0 cloud API key (optional, for cloud mode)
        
        Raises:
            ProviderInitializationError: If Mem0 client initialization fails.
        """
        try:
            from mem0 import Memory
        except ImportError as e:
            raise ImportError(
                "Mem0 library not installed. Install with: pip install mem0ai"
            ) from e
        
        try:
            # Extract default IDs from config
            self.default_user_id = config.get("user_id", "default")
            self.default_agent_id = config.get("agent_id")
            
            # Build Mem0 configuration
            mem0_config = {}
            
            if config.get("llm"):
                mem0_config["llm"] = config["llm"]
            
            if config.get("embedder"):
                mem0_config["embedder"] = config["embedder"]
            
            if config.get("vector_store"):
                mem0_config["vector_store"] = config["vector_store"]
            
            # Initialize Mem0 client
            if mem0_config:
                self.client = Memory.from_config(mem0_config)
            else:
                # Use default configuration
                self.client = Memory()
                
        except Exception as e:
            from . import ProviderInitializationError
            raise ProviderInitializationError(
                "mem0",
                f"Failed to initialize Mem0 client: {str(e)}"
            )
    
    def add_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Add a memory note to Mem0 storage.
        
        Maps MemoryNote fields to Mem0's memory format and stores the memory
        with associated metadata. Extracts user_id and agent_id from the
        memory_note metadata, falling back to config defaults.
        
        Args:
            memory_note: The memory note to store
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message on failure.
        """
        from aios.memory.note import MemoryNote
        
        if not isinstance(memory_note, MemoryNote):
            return MemoryResponse(
                success=False,
                error=f"Expected MemoryNote, got {type(memory_note).__name__}"
            )
        
        try:
            # Extract user_id and agent_id from metadata or use defaults
            user_id = self.default_user_id
            agent_id = self.default_agent_id
            
            # Check if memory_note has metadata attribute with provider-specific params
            if hasattr(memory_note, 'metadata') and memory_note.metadata:
                user_id = memory_note.metadata.get("user_id", user_id)
                agent_id = memory_note.metadata.get("agent_id", agent_id)
            
            # Build metadata for Mem0
            metadata = {
                "keywords": memory_note.keywords,
                "tags": memory_note.tags,
                "category": memory_note.category,
                "context": memory_note.context,
                "timestamp": memory_note.timestamp,
                "memory_note_id": memory_note.id
            }
            
            # Build add parameters
            add_kwargs = {
                "user_id": user_id,
                "metadata": metadata
            }
            
            if agent_id:
                add_kwargs["agent_id"] = agent_id
            
            # Add memory to Mem0
            result = self.client.add(memory_note.content, **add_kwargs)
            
            # Extract memory ID from result
            # Mem0 returns different formats depending on version
            memory_id = None
            if isinstance(result, dict):
                memory_id = result.get("id") or result.get("memory_id")
                # Handle results list format
                if not memory_id and "results" in result:
                    results = result["results"]
                    if results and len(results) > 0:
                        memory_id = results[0].get("id")
            
            # Fall back to original memory_note ID if Mem0 doesn't return one
            memory_id = memory_id or memory_note.id
            
            return MemoryResponse(success=True, memory_id=memory_id)
            
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Mem0 add_memory failed: {str(e)}"
            )
    
    def remove_memory(self, memory_id: str) -> MemoryResponse:
        """Remove a memory from Mem0 by ID.
        
        Args:
            memory_id: Unique identifier of the memory to remove
        
        Returns:
            MemoryResponse with success=True on successful removal,
            or success=False with error message on failure.
        """
        try:
            self.client.delete(memory_id)
            return MemoryResponse(success=True, memory_id=memory_id)
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Mem0 remove_memory failed: {str(e)}"
            )
    
    def update_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Update an existing memory in Mem0.
        
        Args:
            memory_note: The memory note with updated content/metadata
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False with error message on failure.
        """
        from aios.memory.note import MemoryNote
        
        if not isinstance(memory_note, MemoryNote):
            return MemoryResponse(
                success=False,
                error=f"Expected MemoryNote, got {type(memory_note).__name__}"
            )
        
        try:
            # Mem0 update takes memory_id and new data
            self.client.update(memory_note.id, memory_note.content)
            return MemoryResponse(success=True, memory_id=memory_note.id)
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Mem0 update_memory failed: {str(e)}"
            )
    
    def get_memory(self, memory_id: str) -> MemoryResponse:
        """Retrieve a memory from Mem0 by ID.
        
        Args:
            memory_id: Unique identifier of the memory to retrieve
        
        Returns:
            MemoryResponse with success=True, content, and metadata on success,
            or success=False with error message if memory not found.
        """
        if not isinstance(memory_id, str):
            return MemoryResponse(
                success=False,
                error="Memory id must be a string"
            )
        
        try:
            result = self.client.get(memory_id)
            
            if result is None:
                return MemoryResponse(success=False, error="Memory not found")
            
            # Extract content and metadata from Mem0 result
            content = result.get("memory", "") if isinstance(result, dict) else str(result)
            metadata = result.get("metadata", {}) if isinstance(result, dict) else {}
            
            return MemoryResponse(
                success=True,
                content=content,
                metadata={
                    "keywords": metadata.get("keywords", []),
                    "tags": metadata.get("tags", []),
                    "category": metadata.get("category", "Uncategorized"),
                    "timestamp": metadata.get("timestamp", "")
                }
            )
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Mem0 get_memory failed: {str(e)}"
            )
    
    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        """Search for memories in Mem0 matching the query.
        
        Performs semantic search using Mem0's search functionality to find
        memories similar to the query content.
        
        Args:
            query: MemoryQuery containing:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return
                  - params["user_id"]: Optional user ID for scoped search
                  - params["agent_id"]: Optional agent ID for scoped search
        
        Returns:
            MemoryResponse with success=True and search_results on success.
        """
        try:
            content = query.params.get("content", "")
            k = query.params.get("k", 5)
            user_id = query.params.get("user_id", self.default_user_id)
            agent_id = query.params.get("agent_id", self.default_agent_id)
            
            # Build search parameters
            search_kwargs = {
                "user_id": user_id,
                "limit": k
            }
            
            if agent_id:
                search_kwargs["agent_id"] = agent_id
            
            # Search Mem0
            results = self.client.search(content, **search_kwargs)
            
            # Map Mem0 results to standard format
            search_results = []
            
            # Handle different result formats from Mem0
            if isinstance(results, list):
                for item in results[:k]:
                    if isinstance(item, dict):
                        metadata = item.get("metadata", {})
                        search_results.append({
                            "content": item.get("memory", ""),
                            "keywords": metadata.get("keywords", []),
                            "tags": metadata.get("tags", []),
                            "category": metadata.get("category", "Uncategorized"),
                            "timestamp": metadata.get("timestamp", ""),
                            "score": item.get("score")
                        })
            elif isinstance(results, dict) and "results" in results:
                for item in results["results"][:k]:
                    if isinstance(item, dict):
                        metadata = item.get("metadata", {})
                        search_results.append({
                            "content": item.get("memory", ""),
                            "keywords": metadata.get("keywords", []),
                            "tags": metadata.get("tags", []),
                            "category": metadata.get("category", "Uncategorized"),
                            "timestamp": metadata.get("timestamp", ""),
                            "score": item.get("score")
                        })
            
            return MemoryResponse(success=True, search_results=search_results)
            
        except Exception as e:
            return MemoryResponse(
                success=False,
                error=f"Mem0 retrieve_memory failed: {str(e)}"
            )
    
    def retrieve_memory_raw(self, query: MemoryQuery) -> List['MemoryNote']:
        """Retrieve raw memory objects from Mem0 for internal processing.
        
        Similar to retrieve_memory but returns raw MemoryNote objects
        instead of a formatted MemoryResponse.
        
        Args:
            query: MemoryQuery containing:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results (default: 5)
        
        Returns:
            List of MemoryNote objects matching the query.
        """
        from aios.memory.note import MemoryNote
        
        content = query.params.get("content", "")
        k = query.params.get("k", 5)
        user_id = query.params.get("user_id", self.default_user_id)
        agent_id = query.params.get("agent_id", self.default_agent_id)
        
        # Build search parameters
        search_kwargs = {
            "user_id": user_id,
            "limit": k
        }
        
        if agent_id:
            search_kwargs["agent_id"] = agent_id
        
        try:
            results = self.client.search(content, **search_kwargs)
        except Exception:
            return []
        
        # Convert Mem0 results to MemoryNote objects
        memory_notes = []
        
        # Handle different result formats from Mem0
        items = []
        if isinstance(results, list):
            items = results
        elif isinstance(results, dict) and "results" in results:
            items = results["results"]
        
        for item in items[:k]:
            if isinstance(item, dict):
                metadata = item.get("metadata", {})
                memory_note = MemoryNote(
                    content=item.get("memory", ""),
                    id=item.get("id") or metadata.get("memory_note_id"),
                    keywords=metadata.get("keywords", []),
                    tags=metadata.get("tags", []),
                    category=metadata.get("category", "Uncategorized"),
                    context=metadata.get("context", "General"),
                    timestamp=metadata.get("timestamp")
                )
                memory_notes.append(memory_note)
        
        return memory_notes
    
    def close(self) -> None:
        """Clean up Mem0 resources.
        
        Properly disconnects from Mem0 services and releases resources.
        """
        # Mem0 client doesn't require explicit cleanup
        # but we reset the client reference
        self.client = None
