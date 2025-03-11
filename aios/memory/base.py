# This file provides a wrapper on memory access, similarly to working with
# pointers in low level languages
# The memory is organized in blocks of a single byte
from cerebrum.memory.apis import MemoryQuery, MemoryResponse
# Remove the circular import
# from aios.syscall.memory import MemorySyscall
from .retrievers import SimpleEmbeddingRetriever, ChromaRetriever

# use C compatible data types for maximum memory efficiency
import ctypes
from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime

# abstract implementation of memory utilities for thread safe access
class BaseMemoryManager:
    """
    Base implementation of memory management utilities for thread-safe access.
    
    This class provides the core functionality for memory operations in the AIOS system,
    including adding, removing, updating, and retrieving memories. It acts as a wrapper
    for memory access, similar to working with pointers in low-level languages.
    
    The memory system uses ChromaDB as a vector database for efficient semantic retrieval
    of memory notes based on content similarity.
    
    Attributes:
        chroma_retriever (ChromaRetriever): Vector database retriever for storing and 
                                           retrieving memories
        memories (Dict): Dictionary mapping memory IDs to memory objects
    """
    def __init__(self, log_mode):
        """
        Initialize the BaseMemoryManager.
        
        Args:
            log_mode (str): Logging mode for memory operations
        """
        self.chroma_retriever = ChromaRetriever()
        self.memories = {}

    def _analyze_query_to_memory(self, query: MemoryQuery) -> 'MemoryNote':
        """
        Convert a MemoryQuery to a MemoryNote object.
        
        Args:
            query (MemoryQuery): Memory query containing parameters
            
        Returns:
            MemoryNote: Memory note created from query parameters
        """
        from .note import MemoryNote  # Import here to avoid circular dependency
        params = query.params
        valid_keys = ["content", "id", "keywords", "links", "retrieval_count", 
             "timestamp", "last_accessed", "context", "evolution_history", 
             "category", "tags"]
        
        # Extract metadata if present
        metadata = params.get("metadata", {})
        
        # Create a copy of params to avoid modifying the original
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

    def address_request(self, memory_syscall):
        """
        Route a memory syscall to the appropriate method.
        
        Args:
            memory_syscall: Memory syscall object containing the operation and parameters
            
        Raises:
            TypeError: If memory_syscall is not a MemorySyscall
            ValueError: If the operation is invalid
        """
        # Import here to avoid circular dependency
        from aios.syscall.memory import MemorySyscall
        if not isinstance(memory_syscall, MemorySyscall):
            raise TypeError(f"Expected MemorySyscall, got {type(memory_syscall)}")
            
        # memory_note = self._analyze_query_to_memory(memory_syscall.query)
        if memory_syscall.query.operation_type == "add_memory":
            memory_note = self._analyze_query_to_memory(memory_syscall.query)
            return self.add_memory(memory_note)
        elif memory_syscall.query.operation_type == "remove_memory":
            return self.remove_memory(memory_syscall.query.params["memory_id"])
        elif memory_syscall.query.operation_type == "update_memory":
            memory_note = self._analyze_query_to_memory(memory_syscall.query)
            return self.update_memory(memory_note)
        elif memory_syscall.query.operation_type == "get_memory":
            return self.get_memory(memory_syscall.query.params["memory_id"])
        elif memory_syscall.query.operation_type == "retrieve_memory":
            return self.retrieve_memory(memory_syscall.query)
        elif memory_syscall.query.operation_type == "retrieve_memory_raw":
            return self._retrieve_memory_raw(memory_syscall.query)
        else:
            raise ValueError(f"Invalid operation: {memory_syscall.query.operation_type}")

    def add_memory(self, memory_note):
        """
        Add a memory note to the storage.
        
        Args:
            memory_note (MemoryNote): Memory note to add
            
        Returns:
            str: ID of the added memory
            
        Raises:
            TypeError: If memory_note is not a MemoryNote
        """
        from .note import MemoryNote  # Import here to avoid circular dependency
        if not isinstance(memory_note, MemoryNote):
            raise TypeError(f"Expected MemoryNote, got {type(memory_note)}")
            
        metadata = {
            "context": memory_note.context,
            "keywords": memory_note.keywords,
            "tags": memory_note.tags,
            "category": memory_note.category,
            "timestamp": memory_note.timestamp
        }
        self.chroma_retriever.add_document(document=memory_note.content, metadata=metadata, doc_id=memory_note.id)
        self.memories[memory_note.id] = memory_note
        return MemoryResponse(success=True, memory_id=memory_note.id)

    def remove_memory(self, memory_id):
        """
        Remove a memory note from storage.
        
        Args:
            memory_note (MemoryNote): Memory note to remove
            
        Returns:
            bool: True if memory was removed, False if it wasn't found
            
        Raises:
            TypeError: If memory_note is not a MemoryNote
        """
        # memory_id = memory_note.id
        if memory_id in self.memories:
            # Delete from ChromaDB
            self.chroma_retriever.delete_document(memory_id)
            # Delete from local storage
            del self.memories[memory_id]
            return MemoryResponse(success=True, memory_id=memory_id)
        return MemoryResponse(success=False, error="Memory not found")

    def update_memory(self, memory_note):
        """
        Update an existing memory note.
        
        Args:
            memory_note (MemoryNote): Memory note with updated data
            
        Returns:
            MemoryResponse: Response with success status and memory ID
            
        Raises:
            TypeError: If memory_note is not a MemoryNote
        """
        from .note import MemoryNote  # Import here to avoid circular dependency
        if not isinstance(memory_note, MemoryNote):
            raise TypeError(f"Expected MemoryNote, got {type(memory_note)}")
            
        # Get memory_id from the memory_note
        memory_id = memory_note.id
        print("Updating memory with ID:", memory_id)
        print("Current memories:", list(self.memories.keys()))
        
        # Check if the memory exists
        if memory_id not in self.memories:
            print(f"Memory with ID {memory_id} not found in memory store")
            return MemoryResponse(success=False, error="Memory not found")
            
        # Get the existing memory to preserve any fields not provided in the update
        existing_memory = self.memories[memory_id]
        print(f"Found existing memory: {existing_memory.id}")
        
        # Update only the fields that are provided in the memory_note
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
        
        # Save the updated memory
        self.memories[memory_id] = existing_memory
        print(f"Updated memory in memory store: {memory_id}")
        
        # Update in ChromaDB
        metadata = {
            "context": existing_memory.context,
            "keywords": existing_memory.keywords,
            "tags": existing_memory.tags,
            "category": existing_memory.category,
            "timestamp": existing_memory.timestamp
        }
        self.chroma_retriever.delete_document(memory_id)
        self.chroma_retriever.add_document(document=existing_memory.content, metadata=metadata, doc_id=memory_id)
        print(f"Updated memory in ChromaDB: {memory_id}")
        
        return MemoryResponse(success=True, memory_id=memory_id)

    def get_memory(self, memory_id: str) -> 'MemoryNote':
        """
        Retrieve a memory note by ID.
        
        Args:
            memory_id (str): ID of the memory note to retrieve
            
        Returns:
            MemoryNote: Retrieved memory note, or None if not found
            
        Raises:
            TypeError: If memory_id is not a str
        """
        if not isinstance(memory_id, str):
            return MemoryResponse(success=False,error="Memory id must be a string")
        # print("memories: ", self.memories)
        if memory_id not in self.memories:
            return MemoryResponse(success=False,error="Memory not found")
        # print(self.memories[memory_id])
        return MemoryResponse(success=True, content=self.memories[memory_id].content, metadata={'keywords': self.memories[memory_id].keywords, 'tags': self.memories[memory_id].tags, 'category': self.memories[memory_id].category, 'timestamp': self.memories[memory_id].timestamp})
    
    def _retrieve_memory_raw(self, memory_query: MemoryQuery):
        """
        Retrieve memories similar to the query content.
        
        Args:
            memory_query (MemoryQuery): Query containing search content and parameters
            
        Returns:
            List[MemoryNote]: List of memory notes matching the query, limited by k
        """
        # Get results from ChromaDB
        print("memory_query: ", memory_query)
        print("memory_query.params: ", memory_query.params)
        print(type(memory_query.params))
        content = memory_query.params["content"]
        print(type(content))
        if "k" not in memory_query.params:
            k = 5
        else:
            k = memory_query.params["k"]
        chroma_results = self.chroma_retriever.search(content, k)
        retrieved_memories = []
        
        # Process ChromaDB results
        if 'ids' in chroma_results and chroma_results['ids']:
            # Get the first list of IDs (corresponding to our single query)
            doc_ids = chroma_results['ids'][0] if isinstance(chroma_results['ids'][0], list) else chroma_results['ids']
            
            # Process each document ID
            for doc_id in doc_ids:
                memory = self.memories.get(doc_id)
                if memory:
                    retrieved_memories.append(memory)
                
        return retrieved_memories[:k]

    def retrieve_memory(self, memory_query: MemoryQuery):
        """
        Retrieve memories similar to the query content.
        
        Args:
            memory_query (MemoryQuery): Query containing search content and parameters
            
        Returns:
            List[MemoryNote]: List of memory notes matching the query, limited by k
        """
        # Get results from ChromaDB
        content = memory_query.params["content"]
        k = memory_query.params["k"]
        chroma_results = self.chroma_retriever.search(content, k)
        retrieved_memories = []
        
        # Process ChromaDB results
        print("chroma_results", chroma_results)
        
        # ChromaDB returns nested lists, where the first list contains results for each query
        # Since we only have one query, we need to access the first list of IDs
        if 'ids' in chroma_results and chroma_results['ids']:
            # Get the first list of IDs (corresponding to our single query)
            doc_ids = chroma_results['ids'][0] if isinstance(chroma_results['ids'][0], list) else chroma_results['ids']
            
            # Process each document ID
            for doc_id in doc_ids:
                memory = self.memories.get(doc_id)
                if memory:
                    retrieved_memories.append(memory)
        
        retrieved_results = []
        for retrieve_memory in retrieved_memories[:k]:
            retrieved_results.append({
                'content': retrieve_memory.content, 
                'keywords': retrieve_memory.keywords, 
                'tags': retrieve_memory.tags, 
                'category': retrieve_memory.category, 
                'timestamp': retrieve_memory.timestamp
            })
        
        return MemoryResponse(success=True, search_results=retrieved_results)
