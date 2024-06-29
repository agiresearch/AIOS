# aios/memory/

Implements the memory management needed between the agents the LLMs so it can be shared across multiple agents.

## single_memory.py

This takes upon the role of malloc(3) where an agent would be a "process" and each agent only gets one block.

## lru_k_replacer.py

This manages the disk cache using the popular LRU cache replacement algorithm. It counts the amount of times a buffer has been accessed, and if a buffer is rarely used it is evicted when a new buffer needs to be stored.
