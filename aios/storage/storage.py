import os
import json
import pickle

import zlib

from .filesystem.lsfs import LSFS

from cerebrum.storage.apis import StorageResponse

class StorageManager:
    def __init__(self, root_dir, use_vector_db=True, filesystem_type="lsfs"):
        self.use_vector_db = use_vector_db
        self.filesystem_type = filesystem_type
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        if filesystem_type == "lsfs":
            self.filesystem = LSFS(root_dir, use_vector_db)
        
    def address_request(self, agent_request):
        result = self.filesystem.address_request(agent_request)

        # Normalize result to string format for StorageResponse
        # Ensures type safety (prevents ValidationError)
        # Handle empty lists/tuples explicitly first
        if isinstance(result, (list, tuple)) and len(result) == 0:
            result_str = "No documents found"
        elif isinstance(result, (dict, list, tuple)):
            # Prefer JSON for structured types; fallback to str() if not serializable
            try:
                result_str = json.dumps(result)
            except (TypeError, ValueError):
                result_str = str(result)
        elif result is None:
            result_str = "Operation completed with no result"
        elif result == "":
            result_str = "Operation completed successfully"
        else:
            # Ensure we always return a string
            if isinstance(result, (bytes, bytearray)):
                try:
                    result_str = result.decode("utf-8")
                except Exception:
                    result_str = str(result)
            else:
                result_str = str(result)

        return StorageResponse(
            response_message=result_str,
            finished=True
        )
