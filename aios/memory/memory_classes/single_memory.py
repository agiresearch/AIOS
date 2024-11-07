from aios.memory.base import (
    MemoryRequest,
    BaseMemoryManager
)

from typing import Dict, OrderedDict

import pickle
import zlib

from threading import Thread

class SingleMemoryManager:
    def __init__(self, 
                 memory_limit, 
                 eviction_k, 
                 storage_manager):
        self.memory_blocks = dict()
        self.memory_limit = memory_limit
        self.eviction_k = eviction_k
        self.storage_manager = storage_manager
        
    def address_request(self, agent_request):
        operation_type = agent_request.operation_type
        if operation_type == "allocate":
            self.mem_alloc()

    def mem_alloc(self, aid):
        if aid not in self.memory_blocks:
            self.memory_blocks[aid] = OrderedDict()
            self.storage_manager.sto_create(aid)

    def mem_read(self, aid, rid):
        if aid in self.memory_blocks and rid in self.memory_blocks[aid]:
            compressed_data = self.memory_blocks[aid].pop(rid)
            self.memory_blocks[aid][rid] = compressed_data
            return pickle.loads(zlib.decompress(compressed_data))
        else:
            return self.storage_manager.sto_read(aid, rid)

    def mem_write(self, aid, rid, s):
        self.mem_alloc(aid)
        serialized_data = pickle.dumps(s)
        compressed_data = zlib.compress(serialized_data)
        
        if rid in self.memory_blocks[aid]:
            self.memory_blocks[aid].pop(rid)
        self.memory_blocks[aid][rid] = compressed_data

        if self._total_memory_count() > self.memory_limit:
            self._evict_memory(aid)

    def mem_clear(self, aid):
        if aid in self.memory_blocks:
            del self.memory_blocks[aid]
            self.storage_manager.sto_clear(aid)

    def _total_memory_count(self):
        return sum(len(blocks) for blocks in self.memory_blocks.values())

    def _evict_memory(self, aid):
        if aid in self.memory_blocks:
            for _ in range(min(self.eviction_k,
                           len(self.memory_blocks[aid]))):
                rid, compressed_data = self.memory_blocks[aid].popitem(last=False)
                self.storage_manager.sto_write(aid, rid, pickle.loads(zlib.decompress(compressed_data)))
