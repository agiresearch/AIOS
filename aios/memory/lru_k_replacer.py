# Implementation of the LRU_K_Replacer algorithm
# It keeps track of when each buffer to the disk was last used and removes
# the least used buffer when a new buffer is needed

from collections import OrderedDict
from typing import Optional, Dict


class Block_Entry:
    """ sets each block to be removable by default, used for buffers """
    def __init__(self):
        self.hit_count = 0
        self.evictable = True


class LRU_K_Replacer:
    def __init__(self, capacity, k):
        """ initialize the blocks being managed by the LRU_K_Replacer """
        self.replacer_size = capacity
        self.k = k
        self.curr_size = 0
        self.entries: Dict[int, Block_Entry] = {}

        """ counts the amount of times a block has been used in the cache """
        self.hit_list = OrderedDict()

        """ holds the memory block that is being cached by id """
        self.cache_list = OrderedDict()

    def evict(self) -> Optional[int]:
        """ delete the least used block from the cache """
        if self.curr_size == 0:
            return None

        for block_id in reversed(self.hit_list):
            if self.entries[block_id].evictable:
                self.hit_list.pop(block_id)
                self.entries.pop(block_id)
                self.curr_size -= 1
                return block_id

        for block_id in reversed(self.cache_list):
            if self.entries[block_id].evictable:
                self.cache_list.pop(block_id)
                self.entries.pop(block_id)
                self.curr_size -= 1
                return block_id
        return None

    def update_access_history(self, block_id):
        if block_id > self.replacer_size:
            raise ValueError(f"Invalid block_id {block_id}")

        if block_id not in self.entries:
            self.entries[block_id] = Block_Entry()
            self.curr_size += 1

        """ update the amount of times a block has been used in the cache """
        self.entries[block_id].hit_count += 1

        """ cache this value in this script """
        new_count = self.entries[block_id].hit_count

        if new_count == 1:
            self.hit_list[block_id] = None
            self.hit_list.move_to_end(block_id, last=False)
        else:
            if new_count == self.k:
                self.hit_list.pop(block_id)
                self.cache_list[block_id] = None
                self.cache_list.move_to_end(block_id, last=False)
            elif new_count > self.k:
                self.cache_list.move_to_end(block_id, last=False)

    def set_evictable(self, block_id: int, set_evictable: bool) -> None:
        if block_id > self.replacer_size:
            raise ValueError(f"Invalid frame {block_id}")

        if block_id not in self.entries:
            return

        """ modify the amount of blocks that can be evicted accordingly """
        if set_evictable and not self.entries[block_id].evictable:
            self.curr_size += 1
        elif self.entries[block_id].evictable and not set_evictable:
            self.curr_size -= 1

        self.entries[block_id].evictable = set_evictable

    def remove(self, block_id: int) -> None:
        """ remove and modify size of entries dict accordingly """
        if block_id not in self.entries:
            return

        if not self.entries[block_id].evictable:
            raise ValueError(f"Invalid frame {block_id}")

        if self.entries[block_id].hit_count < self.k:
            self.hit_list.pop(block_id)
        else:
            self.cache_list.pop(block_id)

        self.curr_size -= 1
        self.entries.pop(block_id)

    def size(self) -> int:
        return self.curr_size
