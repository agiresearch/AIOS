"""
InHouseProvider - Memory provider using existing AIOS memory implementation.

This provider wraps the existing BaseMemoryManager functionality to maintain
backward compatibility while conforming to the MemoryProvider interface.
It supports both ChromaDB and Qdrant vector backends.
"""
from typing import Dict, Any, List, TYPE_CHECKING
import os

from cerebrum.memory.apis import MemoryQuery, MemoryResponse

from .base import MemoryProvider, _apply_sharing_filter, _enrich_metadata
from aios.memory.retrievers import ChromaRetriever, QdrantRetriever

if TYPE_CHECKING:
    from aios.memory.note import MemoryNote


class InHouseProvider(MemoryProvider):
    """Provider using existing AIOS memory implementation.
    
    This provider maintains all existing functionality including ChromaDB
    and Qdrant vector backend support. When selected, the system behaves
    identically to the current implementation.
    
    Attributes:
        retriever: Vector database retriever (ChromaRetriever or QdrantRetriever)
        memories: Dictionary mapping memory IDs to MemoryNote objects
    """
    
    def __init__(self):
        """Initialize the InHouseProvider with empty state.
        
        The actual retriever is created during initialize() based on config.
        """
        self.retriever = None
        self.memories: Dict[str, 'MemoryNote'] = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration.
        
        Creates the appropriate vector database retriever based on the
        configured backend (ChromaDB or Qdrant).
        
        Args:
            config: Configuration dictionary containing:
                   - vector_db_backend: "chroma" or "qdrant" (default: "chroma")
                   - Additional backend-specific settings
        """
        backend = (
            config.get("vector_db_backend") 
            or os.environ.get("VECTOR_DB_BACKEND") 
            or "chroma"
        ).lower()
        
        if backend == "qdrant":
            self.retriever = QdrantRetriever()
        else:
            self.retriever = ChromaRetriever()
    
    def add_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Add a memory note to storage.
        
        Stores the memory in both the local memories dict and the vector
        database for semantic retrieval.
        
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
            metadata = {
                "context": memory_note.context,
                "keywords": memory_note.keywords,
                "tags": memory_note.tags,
                "category": memory_note.category,
                "timestamp": memory_note.timestamp
            }
            # Preserve cross-agent metadata fields for
            # filtering during retrieval
            for key in (
                "owner_agent",
                "user_id",
                "sharing_policy",
                "memory_type",
            ):
                if key in memory_note.metadata:
                    metadata[key] = memory_note.metadata[key]
            self.retriever.add_document(
                document=memory_note.content, 
                metadata=metadata, 
                doc_id=memory_note.id
            )
            self.memories[memory_note.id] = memory_note
            return MemoryResponse(success=True, memory_id=memory_note.id)
        except Exception as e:
            return MemoryResponse(
                success=False, 
                error=f"Failed to add memory: {str(e)}"
            )
    
    def remove_memory(self, memory_id: str) -> MemoryResponse:
        """Remove a memory by ID.
        
        Removes the memory from both the local memories dict and the
        vector database.
        
        Args:
            memory_id: Unique identifier of the memory to remove
        
        Returns:
            MemoryResponse with success=True on successful removal,
            or success=False if memory not found.
        """
        if memory_id in self.memories:
            try:
                self.retriever.delete_document(memory_id)
                del self.memories[memory_id]
                return MemoryResponse(success=True, memory_id=memory_id)
            except Exception as e:
                return MemoryResponse(
                    success=False, 
                    error=f"Failed to remove memory: {str(e)}"
                )
        return MemoryResponse(success=False, error="Memory not found")
    
    def update_memory(self, memory_note: 'MemoryNote') -> MemoryResponse:
        """Update an existing memory.
        
        Updates the memory in both the local memories dict and the vector
        database. Only provided fields are updated; others are preserved.
        
        Args:
            memory_note: The memory note with updated content/metadata
        
        Returns:
            MemoryResponse with success=True and memory_id on success,
            or success=False if memory not found.
        """
        from aios.memory.note import MemoryNote
        
        if not isinstance(memory_note, MemoryNote):
            return MemoryResponse(
                success=False, 
                error=f"Expected MemoryNote, got {type(memory_note).__name__}"
            )
        
        memory_id = memory_note.id
        
        if memory_id not in self.memories:
            return MemoryResponse(success=False, error="Memory not found")
        
        try:
            # Get existing memory to preserve fields not in update
            existing_memory = self.memories[memory_id]
            
            # Update only provided fields
            if memory_note.content is not None:
                existing_memory.content = memory_note.content
            if memory_note.keywords:
                existing_memory.keywords = memory_note.keywords
            if memory_note.tags:
                existing_memory.tags = memory_note.tags
            if memory_note.category:
                existing_memory.category = memory_note.category
            
            # Update timestamp
            existing_memory.timestamp = memory_note.timestamp or existing_memory.timestamp
            
            # Save updated memory
            self.memories[memory_id] = existing_memory
            
            # Update vector database
            metadata = {
                "context": existing_memory.context,
                "keywords": existing_memory.keywords,
                "tags": existing_memory.tags,
                "category": existing_memory.category,
                "timestamp": existing_memory.timestamp
            }
            self.retriever.delete_document(memory_id)
            self.retriever.add_document(
                document=existing_memory.content, 
                metadata=metadata, 
                doc_id=memory_id
            )
            
            return MemoryResponse(success=True, memory_id=memory_id)
        except Exception as e:
            return MemoryResponse(
                success=False, 
                error=f"Failed to update memory: {str(e)}"
            )
    
    def get_memory(self, memory_id: str) -> MemoryResponse:
        """Retrieve a memory by ID.
        
        Args:
            memory_id: Unique identifier of the memory to retrieve
        
        Returns:
            MemoryResponse with success=True, content, and metadata on success,
            or success=False if memory not found.
        """
        if not isinstance(memory_id, str):
            return MemoryResponse(
                success=False, 
                error="Memory id must be a string"
            )
        
        if memory_id not in self.memories:
            return MemoryResponse(success=False, error="Memory not found")
        
        memory = self.memories[memory_id]
        metadata = {
            'keywords': memory.keywords,
            'tags': memory.tags,
            'category': memory.category,
            'timestamp': memory.timestamp
        }
        # Cross-agent fields let the MemoryManager check access
        # before id-based operations.
        for key in (
            "owner_agent",
            "user_id",
            "sharing_policy",
            "memory_type",
        ):
            metadata[key] = (memory.metadata or {}).get(key, "")
        return MemoryResponse(
            success=True, 
            content=memory.content, 
            metadata=metadata
        )
    
    def retrieve_memory(self, query: MemoryQuery) -> MemoryResponse:
        """Search for memories matching the query.
        
        Performs semantic search using the vector database to find
        memories similar to the query content.  Results are filtered
        by cross-agent sharing rules when ``agent_name``,
        ``user_id``, or ``sharing_policy`` are present in
        ``query.params``.
        
        Args:
            query: MemoryQuery containing:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results to return
                  - params["agent_name"]: (optional) requesting agent
                  - params["user_id"]: (optional) user-scope filter
                  - params["sharing_policy"]: (optional) policy filter
        
        Returns:
            MemoryResponse with success=True and search_results on success.
        """
        try:
            content = query.params["content"]
            k = query.params.get("k", 5)
            agent_name = query.params.get("agent_name")
            user_id = query.params.get("user_id")
            sharing_policy = query.params.get("sharing_policy")
            
            retrieved_results = self.retriever.search(content, k)
            retrieved_memories = []
            
            # Process retrieved results
            if 'ids' in retrieved_results and retrieved_results['ids']:
                # Get the first list of IDs (corresponding to our single query)
                doc_ids = (
                    retrieved_results['ids'][0] 
                    if isinstance(retrieved_results['ids'][0], list) 
                    else retrieved_results['ids']
                )
                
                # Process each document ID
                for doc_id in doc_ids:
                    memory = self.memories.get(doc_id)
                    if memory:
                        retrieved_memories.append(memory)
            
            # Apply cross-agent sharing filter when agent_name
            # is available (injected by MemoryManager)
            if agent_name is not None:
                retrieved_memories = _apply_sharing_filter(
                    retrieved_memories,
                    agent_name,
                    user_id,
                    sharing_policy,
                    lambda note: note.metadata,
                )
            
            # Format results, respecting k on filtered set
            search_results = []
            for memory in retrieved_memories[:k]:
                meta = _enrich_metadata(
                    dict(memory.metadata)
                )
                search_results.append({
                    'content': memory.content,
                    'keywords': memory.keywords,
                    'tags': memory.tags,
                    'category': memory.category,
                    'timestamp': memory.timestamp,
                    'metadata': meta,
                })
            
            return MemoryResponse(
                success=True, search_results=search_results
            )
        except Exception as e:
            return MemoryResponse(
                success=False, 
                error=f"Failed to retrieve memory: {str(e)}"
            )
    
    def retrieve_memory_raw(self, query: MemoryQuery) -> List['MemoryNote']:
        """Retrieve raw memory objects for internal processing.
        
        Similar to retrieve_memory but returns raw MemoryNote objects
        instead of a formatted MemoryResponse.  Results are filtered
        by cross-agent sharing rules when ``agent_name``,
        ``user_id``, or ``sharing_policy`` are present in
        ``query.params``.
        
        Args:
            query: MemoryQuery containing:
                  - params["content"]: The search query text
                  - params["k"]: Maximum number of results (default: 5)
                  - params["agent_name"]: (optional) requesting agent
                  - params["user_id"]: (optional) user-scope filter
                  - params["sharing_policy"]: (optional) policy filter
        
        Returns:
            List of MemoryNote objects matching the query.
        """
        content = query.params["content"]
        k = query.params.get("k", 5)
        agent_name = query.params.get("agent_name")
        user_id = query.params.get("user_id")
        sharing_policy = query.params.get("sharing_policy")
        
        search_results = self.retriever.search(content, k)
        retrieved_memories = []
        
        if 'ids' in search_results and search_results['ids']:
            # Get the first list of IDs (corresponding to our single query)
            doc_ids = (
                search_results['ids'][0] 
                if isinstance(search_results['ids'][0], list) 
                else search_results['ids']
            )
            
            # Process each document ID
            for doc_id in doc_ids:
                memory = self.memories.get(doc_id)
                if memory:
                    retrieved_memories.append(memory)
        
        # Apply cross-agent sharing filter when agent_name
        # is available (injected by MemoryManager)
        if agent_name is not None:
            retrieved_memories = _apply_sharing_filter(
                retrieved_memories,
                agent_name,
                user_id,
                sharing_policy,
                lambda note: note.metadata,
            )
        
        # Enrich metadata on each MemoryNote and respect k
        for memory in retrieved_memories[:k]:
            _enrich_metadata(memory.metadata)
        
        return retrieved_memories[:k]
    
    def close(self) -> None:
        """Clean up resources.
        
        For InHouseProvider, this is a no-op for backward compatibility
        as the existing implementation doesn't require explicit cleanup.
        """
        pass
