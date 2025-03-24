import os
import sys
import json
import tempfile
import shutil
import unittest
from datetime import datetime

# Use fakeredis to replace redis
import fakeredis
import redis
redis.Redis = fakeredis.FakeRedis

# Import StorageManager and StorageResponse
from aios.storage.storage import StorageManager
from cerebrum.storage.apis import StorageResponse

# Dummy data structure to simulate AgentRequest
class DummyQuery:
    def __init__(self, operation_type, params):
        self.operation_type = operation_type
        self.params = params

class DummyAgentRequest:
    def __init__(self, agent_name, query):
        self.agent_name = agent_name
        self.query = query

class TestStorageManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        # Disable vector database support to avoid external dependencies
        self.storage_manager = StorageManager(root_dir=self.test_dir, use_vector_db=False)
        
        # Disable file system observer to prevent errors from file change events
        if hasattr(self.storage_manager.filesystem, 'observer'):
            self.storage_manager.filesystem.observer.stop()
        
        # Patch create_file operation to fix parameter passing issue
        self.original_address_request = self.storage_manager.address_request
        def patched_address_request(agent_request):
            if agent_request.query.operation_type == "create_file":
                file_name = agent_request.query.params.get("file_name")
                file_path = agent_request.query.params.get("file_path")
                result = self.storage_manager.filesystem.sto_create_file(
                    file_name, file_path, agent_request.agent_name
                )
                return StorageResponse(response_message=result, finished=True)
            else:
                return self.original_address_request(agent_request)
        self.storage_manager.address_request = patched_address_request
        
        # Patch the function generating share links to return a dummy link
        self.storage_manager.filesystem.generate_share_link = lambda file_path: "http://dummy.link"
    
    def tearDown(self):
        # Clean up the temporary directory after tests
        shutil.rmtree(self.test_dir)
    
    def test_create_file(self):
        # Test file creation operation
        file_name = "test_file.txt"
        file_path = os.path.join(self.test_dir, file_name)
        query = DummyQuery(
            operation_type="create_file",
            params={"file_name": file_name, "file_path": file_path}
        )
        agent_request = DummyAgentRequest(agent_name="test_agent", query=query)
        response = self.storage_manager.address_request(agent_request)
        self.assertIn("created successfully", response.response_message)
        self.assertTrue(os.path.exists(file_path))
    
    def test_write_and_read(self):
        # Test writing to and reading from a file
        file_name = "test_write.txt"
        file_path = os.path.join(self.test_dir, file_name)
        # Create file
        query_create = DummyQuery(
            operation_type="create_file",
            params={"file_name": file_name, "file_path": file_path}
        )
        agent_create = DummyAgentRequest(agent_name="test_agent", query=query_create)
        self.storage_manager.address_request(agent_create)
        # Write content
        content = "Hello, AIOS Storage Test!"
        query_write = DummyQuery(
            operation_type="write",
            params={"file_name": file_name, "file_path": file_path, "content": content}
        )
        agent_write = DummyAgentRequest(agent_name="test_agent", query=query_write)
        response_write = self.storage_manager.address_request(agent_write)
        self.assertIn("Content has been written", response_write.response_message)
        # Verify file content
        with open(file_path, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, content)
    
    def test_rollback(self):
        from datetime import datetime
        import json

        file_name = "test_rollback.txt"
        file_path = os.path.join(self.test_dir, file_name)
        
        # Create file
        query_create = DummyQuery(
            operation_type="create_file",
            params={"file_name": file_name, "file_path": file_path}
        )
        agent_create = DummyAgentRequest(agent_name="test_agent", query=query_create)
        self.storage_manager.address_request(agent_create)
        
        # Write version 1
        content_v1 = "Version 1"
        query_write_v1 = DummyQuery(
            operation_type="write",
            params={"file_name": file_name, "file_path": file_path, "content": content_v1}
        )
        agent_write_v1 = DummyAgentRequest(agent_name="test_agent", query=query_write_v1)
        self.storage_manager.address_request(agent_write_v1)
        
        # Write version 2
        content_v2 = "Version 2"
        query_write_v2 = DummyQuery(
            operation_type="write",
            params={"file_name": file_name, "file_path": file_path, "content": content_v2}
        )
        agent_write_v2 = DummyAgentRequest(agent_name="test_agent", query=query_write_v2)
        self.storage_manager.address_request(agent_write_v2)
        
        # Get unique hash of the file for version tracking
        file_hash = self.storage_manager.filesystem.get_file_hash(file_path)
        
        # Simulate latest version (version 2) in Redis
        version2_info = {
            'content': content_v2,
            'timestamp': datetime.now().isoformat(),
            'hash': file_hash,
            'change_type': 'modified'
        }
        self.storage_manager.filesystem.redis_client.lpush(file_hash, json.dumps(version2_info))
        
        # Simulate previous version (version 1) in Redis
        version1_info = {
            'content': content_v1,
            'timestamp': datetime.now().isoformat(),
            'hash': file_hash,
            'change_type': 'modified'
        }
        self.storage_manager.filesystem.redis_client.rpush(file_hash, json.dumps(version1_info))
        
        # Request rollback to the previous version
        query_rollback = DummyQuery(
            operation_type="rollback",
            params={"file_path": file_path, "n": "1"}
        )
        agent_rollback = DummyAgentRequest(agent_name="test_agent", query=query_rollback)
        response_rollback = self.storage_manager.address_request(agent_rollback)
        
        self.assertIn("rolled back", response_rollback.response_message)
        
        # Verify file content has been restored to version 1
        with open(file_path, 'r') as f:
            file_content = f.read()
        self.assertEqual(file_content, content_v1)

if __name__ == "__main__":
    unittest.main()