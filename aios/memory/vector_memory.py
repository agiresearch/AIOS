from typing import List, Dict, Any, Optional
import chromadb
from dataclasses import dataclass
import uuid
from datetime import datetime

from .base import BaseMemoryManager, MemoryRequest
from aios.hooks.syscall import useSysCall
from cerebrum.llm.communication import LLMQuery

@dataclass
class VectorMemoryConfig:
    collection_name: str = "default_collection"
    chroma_path: str = "./chroma_db"
    memory_limit: int = 104857600  # 100MB
    eviction_k: int = 10

class VectorMemoryManager(BaseMemoryManager):
    def __init__(self, config: VectorMemoryConfig = None):
        self.config = config or VectorMemoryConfig()
        self.client = chromadb.PersistentClient(path=self.config.chroma_path)
        self.collection = self.client.get_or_create_collection(self.config.collection_name)
        self.syscall = useSysCall()

    def mem_write(self, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a new memory item with vector embedding"""
        memory_id = str(uuid.uuid4())
        
        # Get embedding using LLM query
        query = LLMQuery(
            messages=[{"role": "system", "content": content}],
            operation_type="embedding"
        )
        result = self.syscall.llm(agent_id, query)
        vector = result["response"]["embedding"]

        # Add to ChromaDB
        full_metadata = {
            "text": content,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self.collection.add(
            embeddings=[vector],
            ids=[memory_id],
            metadatas=[full_metadata]
        )
        
        return {"memory_id": memory_id, "status": "success"}

    def mem_read(self, agent_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant memories using semantic similarity"""
        # Get query embedding
        query_obj = LLMQuery(
            messages=[{"role": "system", "content": query}],
            operation_type="embedding"
        )
        result = self.syscall.llm(agent_id, query_obj)
        query_vector = result["response"]["embedding"]

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit
        )
        
        memories = []
        for i in range(len(results['ids'][0])):
            memories.append({
                "id": results['ids'][0][i],
                "content": results['metadatas'][0][i].get("text", ""),
                "metadata": results['metadatas'][0][i],
                "score": results['distances'][0][i] if 'distances' in results else None
            })
        return memories

    def mem_clear(self, memory_id: str = None) -> bool:
        """Clear specific memory or entire collection"""
        if memory_id:
            self.collection.delete(ids=[memory_id])
        else:
            self.client.delete_collection(self.config.collection_name)
            self.collection = self.client.get_or_create_collection(self.config.collection_name)
        return True

    def execute_operation(self, memory_request: MemoryRequest):
        """Execute memory operations based on request type"""
        operation_type = memory_request.operation_type
        if operation_type == "write":
            return self.mem_write(
                agent_id=memory_request.agent_id,
                content=memory_request.content
            )
        elif operation_type == "read":
            return self.mem_read(
                agent_id=memory_request.agent_id,
                query=memory_request.content
            )
        elif operation_type == "clear":
            return self.mem_clear(
                memory_id=memory_request.content if memory_request.content else None
            )
