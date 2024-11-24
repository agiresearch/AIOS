from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class ToolLayer:
    allowed_tools: Optional[List[str]] = None
    custom_tools: Optional[Dict[str, Any]] = None