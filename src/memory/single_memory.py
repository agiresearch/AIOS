from src.memory.base import (
    MemoryRequest,
    BaseMemoryManager
)
import heapq

from queue import Queue, Empty

from utils.compressor import (
    ZLIBCompressor
)

from src.memory.base import (
    Memory
)

from threading import Thread

class UniformedMemoryManager(BaseMemoryManager):
    def __init__(self, max_memory_block_size, memory_block_num):
        super().__init__(max_memory_block_size, memory_block_num)
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
        heapq.heapify(self.free_memory_blocks)
        self.memory_operation_queue = Queue() # TODO add lock to ensure parallel

    def run(self):
        while self.active:
            try:
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
        compressed_content = self.compressor.compress(content)
        size = len(compressed_content)
        address = self.memory_blocks[
            self.aid_to_memory[agent_id][round_id]["memory_block_id"]
        ].mem_alloc(size)

        self.memory_blocks[
            self.aid_to_memory[agent_id][round_id]["memory_block_id"]
        ].mem_write(address, compressed_content)

    def mem_read(self, agent_id, round_id):
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
        self.aid_to_mid.pop(agent_id)
        heapq.heappush(agent_id)
