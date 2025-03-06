# This file provides a wrapper on memory access, similarly to working with
# pointers in low level languages
# The memory is organized in blocks of a single byte
from Cerebrum.cerebrum.memory.apis import MemoryQuery
from aios.syscall.memory import MemorySyscall
from .retrievers import SimpleEmbeddingRetriever, ChromaRetriever

# use C compatible data types for maximum memory efficiency
import ctypes
from typing import Dict, Any, Optional


class MemoryNote:
    """A memory note that represents a single unit of information in the memory system.
    
    This class encapsulates all metadata associated with a memory, including:
    - Core content and identifiers
    - Temporal information (creation and access times)
    - Semantic metadata (keywords, context, tags)
    - Relationship data (links to other memories)
    - Usage statistics (retrieval count)
    - Evolution tracking (history of changes)
    """
    
    def __init__(self, 
                 content: str,
                 id: Optional[str] = None,
                 keywords: Optional[List[str]] = None,
                 links: Optional[Dict] = None,
                 retrieval_count: Optional[int] = None,
                 timestamp: Optional[str] = None,
                 last_accessed: Optional[str] = None,
                 context: Optional[str] = None,
                 evolution_history: Optional[List] = None,
                 category: Optional[str] = None,
                 tags: Optional[List[str]] = None):
        """Initialize a new memory note with its associated metadata.
        
        Args:
            content (str): The main text content of the memory
            id (Optional[str]): Unique identifier for the memory. If None, a UUID will be generated
            keywords (Optional[List[str]]): Key terms extracted from the content
            links (Optional[Dict]): References to related memories
            retrieval_count (Optional[int]): Number of times this memory has been accessed
            timestamp (Optional[str]): Creation time in format YYYYMMDDHHMM
            last_accessed (Optional[str]): Last access time in format YYYYMMDDHHMM
            context (Optional[str]): The broader context or domain of the memory
            evolution_history (Optional[List]): Record of how the memory has evolved
            category (Optional[str]): Classification category
            tags (Optional[List[str]]): Additional classification tags
        """
        # Core content and ID
        self.content = content
        self.id = id or str(uuid.uuid4())
        
        # Semantic metadata
        self.keywords = keywords or []
        self.links = links or []
        self.context = context or "General"
        self.category = category or "Uncategorized"
        self.tags = tags or []
        
        # Temporal information
        current_time = datetime.now().strftime("%Y%m%d%H%M")
        self.timestamp = timestamp or current_time
        self.last_accessed = last_accessed or current_time
        
        # Usage and evolution data
        self.retrieval_count = retrieval_count or 0
        self.evolution_history = evolution_history or []

    def return_params(self) -> Dict[str, Any]:
        return {
            "content": self.content or "",
            "id": self.id or "",
            "keywords": self.keywords or [],
            "links": self.links or [],
            "retrieval_count": self.retrieval_count or 0,
            "timestamp": self.timestamp or "",
            "last_accessed": self.last_accessed or "",
            "context": self.context or "",
            "evolution_history": self.evolution_history or [],
            "category": self.category or "",
            "tags": self.tags or []
        }

# abstract implementation of memory utilities for thread safe access
class BaseMemoryManager:
    def __init__(self):
        self.chroma_retriever = ChromaRetriever()
        self.memories = {}

    def _analyze_query_to_memory(self, query: MemoryQuery) -> MemoryNote:
        params = query.params
        valid_keys = ["content", "id", "keywords", "links", "retrieval_count", 
             "timestamp", "last_accessed", "context", "evolution_history", 
             "category", "tags"]
        filtered_data = {k: params[k] for k in params if k in valid_keys}
        memory_note = MemoryNote(**filtered_data)
        return memory_note

    def address_request(self, memory_syscall: MemorySyscall):
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

    def add_memory(self, memory_note: MemoryNote):
        metadata = {
            "context": memory_note.context,
            "keywords": memory_note.keywords,
            "tags": memory_note.tags,
            "category": memory_note.category,
            "timestamp": memory_note.timestamp
        }
        self.chroma_retriever.add_document(document=memory_note.content, metadata=metadata, doc_id=memory_note.id)
        return memory_note.id

    def remove_memory(self, memory_note: MemoryNote):
        memory_id = memory_note.id
        if memory_id in self.memories:
            # Delete from ChromaDB
            self.chroma_retriever.delete_document(memory_id)
            # Delete from local storage
            del self.memories[memory_id]
            return True
        return False

    def update_memory(self, memory_note: MemoryNote):
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

    def get_memory(self, memory_note: MemoryNote):
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


