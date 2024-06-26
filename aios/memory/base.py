# This file provides a wrapper on memory access, similarly to working with
# pointers in low level languages
# The memory is organized in blocks of a single byte


# use C compatible data types for maximum memory efficiency
import ctypes

class MemoryRequest:
    def __init__(self, agent_id: int, round_id: int, operation_type: str, content: str = None):
        self.agent_id = agent_id
        self.round_id = round_id
        self.content = content
        self.operation_type = operation_type

class Memory:
    def __init__(self, size=1024):
        self.size = size
        """ makes an array of bytes, typically how memory is organized """
        self.memory = (ctypes.c_ubyte * size)()
        self.free_blocks = [(0, size - 1)]

    # malloc(3) implementation
    def mem_alloc(self, size):
        for i, (start, end) in enumerate(self.free_blocks):
            block_size = end - start + 1
            if block_size >= size:
                allocated_start = start
                allocated_end = start + size - 1
                if allocated_end == end:
                    self.free_blocks.pop(i)
                else:
                    self.free_blocks[i] = (allocated_end + 1, end)
                return allocated_start
        raise MemoryError("No sufficient memory available.")

    def mem_clear(self, start, size):
        allocated_end = start + size - 1
        self.free_blocks.append((start, allocated_end))
        self.free_blocks.sort()

    # memcpy(3) implementation
    def mem_write(self, address, data):
        size = len(data)
        if address + size > self.size:
            raise MemoryError("Not enough space to write data.")
        for i in range(size):
            self.memory[address + i] = data[i]

    # similar to dereferencing pointers
    def mem_read(self, address, size):
        data = self.memory[address:address + size]
        return data

# abstract implementation of memory utilities for thread safe access
class BaseMemoryManager:
    def __init__(self, max_memory_block_size, memory_block_num):
        pass

    def run(self):
        pass

    def start(self):
        """start the scheduler"""
        self.active = True
        self.thread.start()

    def stop(self):
        """stop the scheduler"""
        self.active = False
        self.thread.join()

    def mem_write(self, content: str):
        pass

    def mem_read(self, agent_id):
        pass

    def mem_alloc(self, agent_id):
        pass

    def mem_clear(self):
        pass
