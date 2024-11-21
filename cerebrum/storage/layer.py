from dataclasses import dataclass
from typing import Any, Dict, Optional

@dataclass
class StorageLayer:
    root_dir: str = "root"
    use_vector_db: bool = False
    vector_db_config: Optional[Dict[str, Any]] = None