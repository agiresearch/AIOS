from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class OverridesLayer:
    log_mode: str = "console"
    max_workers: int = 64
    custom_syscalls: Optional[Dict[str, Any]] = None