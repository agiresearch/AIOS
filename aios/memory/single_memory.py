# This file makes it easier for threads to access memory for each agent by
# placing a lock on memory that needs to be read later. This is implemented as
# wrapper upon the access methods in BaseMemoryManager

from aios.memory.base import (
    MemoryRequest,
    BaseMemoryManager
)

# allows for lists to be heapify'd so the blocks are in order
import heapq

# FIFO queue for whichever thread stops blocking first
from queue import Queue, Empty

from utils.compressor import (
    ZLIBCompressor
)

from aios.memory.base import (
    Memory
)

from threading import Thread

from typing import List, Dict, Any, Optional
import chromadb
from dataclasses import dataclass
import uuid
from datetime import datetime

from aios.hooks.syscall import useSysCall
from cerebrum.llm.communication import LLMQuery
from sentence_transformers import SentenceTransformer


class UniformedMemoryManager(BaseMemoryManager):
    def __init__(self, max_memory_block_size, memory_block_num):
        super().__init__(max_memory_block_size, memory_block_num)
        """ initiate the memory manager in a manner similar to malloc(3) """
        self.memory_blocks = [
            Memory(max_memory_block_size) for _ in range(memory_block_num)
        ]
        self.free_memory_blocks = [i for i in range(0, memory_block_num)]
        self.thread = Thread(target=self.run)

        self.aid_to_memory = dict() # map agent id to memory block id, address, size
        # {
        #    agent_id: {
        #       round_id: {"memory_block_id": int, "address": int, size: int}
        #    }
        # }

        self.compressor = ZLIBCompressor() # used for compressing data
        """ maintain a min heap structure for free memory blocks """
        heapq.heapify(self.free_memory_blocks)
        self.memory_operation_queue = Queue() # TODO add lock to ensure parallel

    def run(self):
        while self.active:
            try:
                """ give a reasonable timeout between iterations here """
                memory_request = self.memory_operation_queue.get(block=True, timeout=0.1)
                self.execute_operation(memory_request)
            except Empty:
                pass

    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def execute_operation(self, memory_request: MemoryRequest):
        operation_type = memory_request.operation_type
        if operation_type == "write":
            self.mem_write(
                agent_id=memory_request.agent_id, content=memory_request.content
            )
        elif operation_type == "read":
            self.mem_read(
                agent_id=memory_request.agent_id, round_id=memory_request.round_id
            )

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def mem_write(self, agent_id, round_id: str, content: str):
        """ write to memory given agent id """
        compressed_content = self.compressor.compress(content)
        size = len(compressed_content)
        address = self.memory_blocks[
            self.aid_to_memory[agent_id][round_id]["memory_block_id"]
        ].mem_alloc(size)

        self.memory_blocks[
            self.aid_to_memory[agent_id][round_id]["memory_block_id"]
        ].mem_write(address, compressed_content)

    def mem_read(self, agent_id, round_id):
        """ read memory given agent id """
        memory_block_id = self.aid_to_memory[agent_id][round_id]
        data = self.memory_blocks[memory_block_id].mem_read(
            self.aid_to_memory[agent_id][round_id]["address"],
            self.aid_to_memory[agent_id][round_id]["size"]
        )
        return data

    def mem_alloc(self, agent_id):
        memory_block_id = heapq.heappop(self.free_memory_blocks)
        self.aid_to_memory[agent_id] = {
            "memory_block_id": memory_block_id
        }

    def mem_clear(self, agent_id):
        memory_block = self.aid_to_memory.pop(agent_id)
        memory_block_id = memory_block['memory_block_id']
        heapq.heappush(self.free_memory_blocks, memory_block_id)


@dataclass
class VectorMemoryConfig:
    collection_name: str = "default_collection"
    chroma_path: str = "./chroma_db"
    memory_limit: int = 104857600  # 100MB
    eviction_k: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"  # Default small but effective model

class VectorMemoryManager(BaseMemoryManager):
    def __init__(self, config: VectorMemoryConfig = None):
        self.config = config or VectorMemoryConfig()
        # Initialize ChromaDB with built-in embeddings
        self.client = chromadb.PersistentClient(path=self.config.chroma_path)
        self.collection = self.client.get_or_create_collection(
            name=self.config.collection_name,
            embedding_function=chromadb.embeddings.SentenceTransformerEmbeddingFunction(
                model_name=self.config.embedding_model
            )
        )

    def mem_write(self, agent_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a new memory item with vector embedding"""
        memory_id = str(uuid.uuid4())
        
        # Add to ChromaDB - it will handle embedding generation internally
        full_metadata = {
            "text": content,
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            **(metadata or {})
        }
        
        self.collection.add(
            documents=[content],  # ChromaDB will generate embeddings
            ids=[memory_id],
            metadatas=[full_metadata]
        )
        
        return {"memory_id": memory_id, "status": "success"}

    def mem_read(self, agent_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant memories using semantic similarity"""
        # Search in ChromaDB - it will handle query embedding internally
        results = self.collection.query(
            query_texts=[query],
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
            self.collection = self.client.get_or_create_collection(
                name=self.config.collection_name,
                embedding_function=chromadb.embeddings.SentenceTransformerEmbeddingFunction(
                    model_name=self.config.embedding_model
                )
            )
        return True

    def execute_operation(self, memory_request: MemoryRequest):
        """Execute memory operations based on request type"""
        operation_type = memory_request.operation_type
        if operation_type == "write":
            return self.mem_write(
                agent_id=memory_request.agent_id,
                content=memory_request.content,
                metadata=memory_request.metadata
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
