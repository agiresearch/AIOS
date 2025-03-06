# This file provides a wrapper on memory access, similarly to working with
# pointers in low level languages
# The memory is organized in blocks of a single byte
from cerebrum.memory.apis import MemoryQuery
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
    def __init__(self,log_mode):
        self.chroma_retriever = ChromaRetriever()
        self.memories = {}

    def _analyze_query_to_memory(self, query: MemoryQuery) -> 'MemoryNote':
        from .note import MemoryNote  # Import here to avoid circular dependency
        params = query.params
        valid_keys = ["content", "id", "keywords", "links", "retrieval_count", 
             "timestamp", "last_accessed", "context", "evolution_history", 
             "category", "tags"]
        filtered_data = {k: params[k] for k in params if k in valid_keys}
        memory_note = MemoryNote(**filtered_data)
        return memory_note

    def address_request(self, memory_syscall):
        # Import here to avoid circular dependency
        from aios.syscall.memory import MemorySyscall
        if not isinstance(memory_syscall, MemorySyscall):
            raise TypeError(f"Expected MemorySyscall, got {type(memory_syscall)}")
            
        memory_note = self._analyze_query_to_memory(memory_syscall.query)
        if memory_syscall.query.operation == "add_memory":
            self.add_memory(memory_note)
        elif memory_syscall.query.operation == "remove_memory":
            self.remove_memory(memory_note)
        elif memory_syscall.query.operation == "update_memory":
            self.update_memory(memory_note)
        elif memory_syscall.query.operation == "get_memory":
            self.get_memory(memory_note)
        elif memory_syscall.query.operation == "retrieve_memory":
            self.retrieve_memory(memory_syscall.query)
        else:
            raise ValueError(f"Invalid operation: {memory_syscall.query.operation}")

    def add_memory(self, memory_note):
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
        return memory_note.id

    def remove_memory(self, memory_note):
        from .note import MemoryNote  # Import here to avoid circular dependency
        if not isinstance(memory_note, MemoryNote):
            raise TypeError(f"Expected MemoryNote, got {type(memory_note)}")
            
        memory_id = memory_note.id
        if memory_id in self.memories:
            # Delete from ChromaDB
            self.chroma_retriever.delete_document(memory_id)
            # Delete from local storage
            del self.memories[memory_id]
            return True
        return False

    def update_memory(self, memory_note):
        from .note import MemoryNote  # Import here to avoid circular dependency
        if not isinstance(memory_note, MemoryNote):
            raise TypeError(f"Expected MemoryNote, got {type(memory_note)}")
            
        memory_id = memory_note.id
        if memory_id not in self.memories:
            return False
            
        self.memories[memory_id] = memory_note  
        # Update in ChromaDB
        metadata = {
            "context": memory_note.context,
            "keywords": memory_note.keywords,
            "tags": memory_note.tags,
            "category": memory_note.category,
            "timestamp": memory_note.timestamp
        }
        self.chroma_retriever.delete_document(memory_id)
        self.chroma_retriever.add_document(document=memory_note.content, metadata=metadata, doc_id=memory_id)
        
        return True

    def get_memory(self, memory_note):
        from .note import MemoryNote  # Import here to avoid circular dependency
        if not isinstance(memory_note, MemoryNote):
            raise TypeError(f"Expected MemoryNote, got {type(memory_note)}")
            
        memory_id = memory_note.id
        if memory_id not in self.memories:
            return None
        return self.memories[memory_id]

    def retrieve_memory(self, memory_query: MemoryQuery):
        # Get results from ChromaDB
        content = memory_query.params["content"]
        k = memory_query.params["k"]
        chroma_results = self.chroma_retriever.search(content, k)
        retrieved_memories = []
        
        # Process ChromaDB results
        for i, doc_id in enumerate(chroma_results['ids']):
            memory = self.memories.get(doc_id)
            retrieved_memories.append(memory)
                
        return retrieved_memories[:k]
