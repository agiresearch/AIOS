import os
import pickle
import zlib
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import redis
import json
from datetime import datetime
from typing import Dict, Any
import hashlib

from .vector_db import ChromaDB

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, lsfs_instance):
        self.lsfs = lsfs_instance
        
    def on_modified(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "modified")
            
    def on_created(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "created")
            
    def on_deleted(self, event):
        if not event.is_directory:
            self.lsfs.handle_file_change(event.src_path, "deleted")

class LSFS:
    def __init__(self, root_dir, use_vector_db=True, max_versions=20):
        self.root_dir = root_dir
        self.use_vector_db = use_vector_db
        self.max_versions = max_versions
        self.vector_db = ChromaDB(mount_dir=self.root_dir)
        
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True
        )
        
        # Initialize file system observer
        self.observer = Observer()
        self.event_handler = FileChangeHandler(self)
        self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
        self.observer.start()
        
    def __del__(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
            
    def get_file_hash(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def handle_file_change(self, file_path: str, change_type: str):
        try:
            relative_path = os.path.relpath(file_path, self.root_dir)
            
            if change_type in ["modified", "created"]:
                # Read file content
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Update vector DB
                if self.use_vector_db:
                    self.vector_db.update_document(relative_path, content)
                
                # Update Redis cache with version history
                file_hash = self.get_file_hash(file_path)
                timestamp = datetime.now().isoformat()
                
                version_info = {
                    'content': content,
                    'timestamp': timestamp,
                    'hash': file_hash,
                    'change_type': change_type
                }
                
                versions_key = f"file_versions:{relative_path}"
                versions = self.redis_client.lrange(versions_key, 0, -1)
                versions = [json.loads(v) for v in versions]
                
                # Add new version
                self.redis_client.lpush(versions_key, json.dumps(version_info))
                
                # Trim to max versions
                if len(versions) >= self.max_versions:
                    self.redis_client.ltrim(versions_key, 0, self.max_versions - 1)
                    
            elif change_type == "deleted":
                # Remove from vector DB
                if self.use_vector_db:
                    self.vector_db.delete_document(relative_path)
                
                # Add deletion record to Redis
                versions_key = f"file_versions:{relative_path}"
                deletion_info = {
                    'timestamp': datetime.now().isoformat(),
                    'change_type': 'deleted'
                }
                self.redis_client.lpush(versions_key, json.dumps(deletion_info))
                
        except Exception as e:
            print(f"Error handling file change: {str(e)}")
            
    def get_file_history(self, file_path: str, limit: int = None) -> list:
        relative_path = os.path.relpath(file_path, self.root_dir)
        versions_key = f"file_versions:{relative_path}"
        
        limit = limit or self.max_versions
        versions = self.redis_client.lrange(versions_key, 0, limit - 1)
        return [json.loads(v) for v in versions]
        
    def restore_version(self, file_path: str, version_index: int) -> bool:
        try:
            relative_path = os.path.relpath(file_path, self.root_dir)
            versions_key = f"file_versions:{relative_path}"
            
            # Get specified version
            version_data = self.redis_client.lindex(versions_key, version_index)
            if not version_data:
                return False
                
            version_info = json.loads(version_data)
            if 'content' not in version_info:
                return False
                
            # Write content back to file
            with open(file_path, 'w') as f:
                f.write(version_info['content'])
                
            # Update vector DB
            if self.use_vector_db:
                self.vector_db.update_document(relative_path, version_info['content'])
                
            return True
            
        except Exception as e:
            print(f"Error restoring version: {str(e)}")
            return False

    def address_request(self, agent_request):
        collection_name = agent_request.agent_name
        file_operation = agent_request.query.messages[0]        
        
        # results = []
        
        operation_type = file_operation.get("name", "terminal")
        params = file_operation.get("parameters", {})
        
        if operation_type == "mount":
            result = self.sto_mount(agent_request)
        
        elif operation_type == "create_file":
            result = self.sto_create_file(params["name"], collection_name)

        elif operation_type == "create_dir":
            result = self.sto_create_directory(params["name"], collection_name)
            
        elif operation_type == "write":
            result = self.sto_write(params["name"], params["content"], collection_name)
            
        elif operation_type == "read":
            result = self.sto_read(params["name"], collection_name)
        
        elif operation_type == "retrieve":
            result = self.sto_retrieve(
                collection_name,
                params["query_text"],
                params.get("k", "3"),
                params.get("keywords", None)
            )
            
        elif operation_type == "rollback":
            result = self.sto_rollback(
                params["name"],
                params.get("n", "1"),
                params.get("time", None)
            )

        elif operation_type == "link":
            result = self.sto_link(params["name"], collection_name)
                
        # return results[0] if len(results) == 1 else results
        return result

    def sto_create_file(self, file_name: str, collection_name: str = None) -> bool:
        try:
            file_path = os.path.join(self.root_dir, file_name)
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Create empty file
                
                if self.use_vector_db:
                    self.vector_db.update_document(file_path, "", collection_name)
                return True
            return False
        except Exception as e:
            print(f"Error creating file: {str(e)}")
            return False
            
    def sto_create_directory(self, dir_name: str, collection_name: str = None) -> bool:
        try:
            dir_path = os.path.join(self.root_dir, dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                # if self.use_vector_db:
                #     self.vector_db.create_directory(dir_name, collection_name)
                return True
            return False
        
        except Exception as e:
            print(f"Error creating directory: {str(e)}")
            return False
            
    def sto_mount(self, agent_request) -> str:
        try:
            agent_name = agent_request.agent_name
            self.vector_db.add_or_get_collection(agent_name)
            root_dir = agent_request.query.messages[0].get("parameters", {}).get("root", self.root_dir)
            
            self.vector_db.build_database(root_dir)
            response = f"File system mounted successfully for agent: {agent_name}"
            return response
        
        except Exception as e:
            response = f"Error mounting file system: {str(e)}"
            return response
            
    def sto_write(self, file_name: str, content: str, collection_name: str = None) -> bool:
        try:
            file_path = os.path.join(self.root_dir, file_name)
            
            # Write to file
            with open(file_path, 'w') as f:
                f.write(content)
                
            # Update vector DB
            if self.use_vector_db:
                self.vector_db.update_document(file_path, content, collection_name)
                
            # File change handler will handle Redis caching
            self.handle_file_change(file_path, "modified")
            
            return True
        except Exception as e:
            print(f"Error writing to file: {str(e)}")
            return False
            
    def sto_read(self, file_name: str, collection_name: str = None) -> dict:
        try:
            file_path = os.path.join(self.root_dir, file_name)
            
            if not os.path.exists(file_path):
                return {"error": "File not found"}
                
            with open(file_path, 'r') as f:
                content = f.read()
                
            return {
                "content": content,
                "file_name": file_name,
                "file_path": file_path
            }
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return {"error": str(e)}
            
    def sto_retrieve(self, collection_name: str, query_text: str, k: str = "3", keywords: str = None) -> list:
        try:
            collection = self.vector_db.add_or_get_collection(collection_name)
            return self.vector_db.retrieve(collection, query_text, k, keywords)
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []
            
    def sto_rollback(self, file_name: str, n: str = "1", time: str = None) -> bool:
        try:
            file_path = os.path.join(self.root_dir, file_name)
            
            if time:
                # Find version closest to specified time
                versions = self.get_file_history(file_path)
                target_version = None
                min_time_diff = float('inf')
                
                for i, version in enumerate(versions):
                    version_time = datetime.fromisoformat(version['timestamp'])
                    target_time = datetime.fromisoformat(time)
                    time_diff = abs((version_time - target_time).total_seconds())
                    
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        target_version = i
                        
                if target_version is not None:
                    return self.restore_version(file_path, target_version)
            else:
                # Rollback n versions
                return self.restore_version(file_path, int(n) - 1)
                
            return False
        except Exception as e:
            print(f"Error rolling back file: {str(e)}")
            return False
            
    def sto_link(self, file_name: str, collection_name: str = None) -> dict:
        try:
            file_path = os.path.join(self.root_dir, file_name)
            
            if not os.path.exists(file_path):
                return {"error": "File not found"}
                
            if self.use_vector_db:
                link_info = self.vector_db.link_document(file_path, collection_name)
                if link_info:
                    return link_info
                    
            # Fallback to basic file info if vector DB link fails
            return {
                "file_name": file_name,
                "file_path": file_path,
                "last_modified": datetime.fromtimestamp(
                    os.path.getmtime(file_path)
                ).isoformat()
            }
        except Exception as e:
            print(f"Error generating file link: {str(e)}")
            return {"error": str(e)}
