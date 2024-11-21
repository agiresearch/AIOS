from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryLayer:
    memory_limit: int = 104857600  # 100MB
    eviction_k: int = 10
    custom_eviction_policy: Optional[str] = None