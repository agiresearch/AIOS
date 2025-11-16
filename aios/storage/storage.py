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
        #  Ensures type safety (prevents ValidationError) 
        if isinstance(result, dict):
            result_str = json.dumps(result)
        elif result is None:
        result_str = "Operation completed with no result"
        elif result == "":
            result_str = "Operation completed successfully"
        else:
            result_str = str(result)
        # Empty list from retrieve operations should show a meaningful message
        if result_str == "[]":
            result_str = "No documents found"


        return StorageResponse(
            response_message=result_str,
            finished=True
        )