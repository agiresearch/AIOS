import os
import pickle
import zlib
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Set, Optional
import hashlib
import threading
from urllib.parse import urljoin
import uuid
import requests

from .vector_db import ChromaDB

import logging

logging.getLogger('watchdog').setLevel(logging.ERROR)

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
        
        
        # # Test Redis connection
        try:
            self.redis_client.ping()
            print("Successfully connected to Redis")
            self.use_redis = True
            
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}")
            self.use_redis = False
        
        # Initialize file system observer
        self.observer = Observer()
        self.event_handler = FileChangeHandler(self)
        self.observer.schedule(self.event_handler, self.root_dir, recursive=True)
        self.observer.start() # temporarily disabled
        
        # Add file locks dictionary
        self.file_locks = {}
        self.locks_lock = threading.Lock()  # Meta-lock for the locks dictionary
        
        # Add permission management
        self.agent_permissions = {}  # agent_name -> {paths, operations}
        self.permissions_lock = threading.Lock()
        
        # Add priority groups for agents
        self.priority_groups = {}  # group_name -> set(agent_names)
        self.agent_groups = {}     # agent_name -> set(group_names)
        self.groups_lock = threading.Lock()
        
        # Default admin agent with full access
        self.set_agent_permissions("admin", ["*"], ["*"])
        
        # Create default group with admin
        self.create_priority_group("admin_group", "admin")
        
    def __del__(self):
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
            
    def get_file_hash(self, file_path: str) -> str:
        return hashlib.sha256(file_path.encode()).hexdigest()
            
    def get_file_lock(self, file_path: str) -> threading.Lock:
        with self.locks_lock:
            if file_path not in self.file_locks:
                self.file_locks[file_path] = threading.Lock()
            return self.file_locks[file_path]
            
    def handle_file_change(self, file_path: str, change_type: str):
        # """Handle file changes with proper lock management."""
        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=5):  # Add timeout to prevent deadlocks
                try:
                    # relative_path = os.path.relpath(file_path, self.root_dir)
                    file_hash = self.get_file_hash(file_path)
                    
                    if change_type in ["modified", "created"]:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        # Update vector DB
                        if self.use_vector_db:
                            self.vector_db.update_document(file_path, content)
                            
                        # Update Redis cache with version history
                        timestamp = datetime.now().isoformat()
                        
                        version_info = {
                            'content': content,
                            'timestamp': timestamp,
                            'hash': file_hash,
                            'change_type': change_type
                        }
                        
                        # versions_key = f"file_versions:{relative_path}"
                        versions_key = file_hash
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
                            self.vector_db.delete_document(file_path)
                        
                        # Add deletion record to Redis
                        # versions_key = f"file_versions:{relative_path}"
                        versions_key = file_hash
                        deletion_info = {
                            'timestamp': datetime.now().isoformat(),
                            'change_type': 'deleted'
                        }
                        self.redis_client.lpush(versions_key, json.dumps(deletion_info))
                        
                finally:
                    lock.release()  # Ensure lock is always released
            else:
                print(f"Timeout waiting for lock on {file_path}")
        except Exception as e:
            print(f"Error handling file change: {str(e)}")
            
    def get_file_history(self, file_path: str, limit: int = None) -> list:
        # relative_path = os.path.relpath(file_path, self.root_dir)
        # versions_key = f"file_versions:{relative_path}"
        
        file_hash = self.get_file_hash(file_path)
        versions_key = file_hash
        
        limit = limit or self.max_versions
        versions = self.redis_client.lrange(versions_key, 0, limit - 1)
        return [json.loads(v) for v in versions]
        
    def restore_version(self, file_path: str, version_index: int) -> bool:
        # file_lock = self.get_file_lock(file_path)
        
        # with file_lock:
        try:
            # relative_path = os.path.relpath(file_path, self.root_dir)
            # versions_key = f"file_versions:{relative_path}"
            
            file_hash = self.get_file_hash(file_path)
            versions_key = file_hash
            
            # Get specified version
            version_data = self.redis_client.lindex(versions_key, version_index)
            if not version_data:
                return False
                
            version_info = json.loads(version_data)
            if 'content' not in version_info:
                return False
            
            with open(file_path, 'w') as f:
                f.write(version_info['content'])
                
            # Update vector DB
            # if self.use_vector_db:
            #     self.vector_db.update_document(file_path, version_info['content'])
                
            return True
            
        except Exception as e:
            print(f"Error restoring version: {str(e)}")
            return False

    def address_request(self, agent_request):
        collection_name = agent_request.agent_name
        operation_type = agent_request.query.operation_type
        
        if not self.is_agent_registered(collection_name):
            return f"Access denied: Agent '{collection_name}' is not registered"
        
        target_agent = agent_request.query.params.get("target_agent", None)
        
        if target_agent and not self.check_group_access(collection_name, target_agent):
            return f"Permission denied: Agent '{collection_name}' does not have access to agent '{target_agent}' data"
        
        path = None
        if operation_type in ["create_file", "write", "rollback", "share"]:
            path = agent_request.query.params.get("file_path", None)
        elif operation_type == "create_dir":
            path = agent_request.query.params.get("dir_path", None)
            
        if not self.check_permission(collection_name, operation_type, path):
            return f"Permission denied: Agent '{collection_name}' does not have permission to perform '{operation_type}' on '{path}'"
        
        # Handle group management operations
        if operation_type == "create_group":
            group_name = agent_request.query.params.get("group_name", None)
            return self.create_priority_group(group_name, collection_name)
            
        elif operation_type == "add_to_group":
            group_name = agent_request.query.params.get("group_name", None)
            agent_name = agent_request.query.params.get("agent_name", None)
            return self.add_agent_to_group(group_name, agent_name, collection_name)
            
        elif operation_type == "remove_from_group":
            group_name = agent_request.query.params.get("group_name", None)
            agent_name = agent_request.query.params.get("agent_name", None)
            return self.remove_agent_from_group(group_name, agent_name, collection_name)
            
        elif operation_type == "get_groups":
            return self.get_agent_groups(collection_name)
            
        elif operation_type == "get_group_members":
            group_name = agent_request.query.params.get("group_name", None)
            return self.get_group_members(group_name, collection_name)
        
        # Handle regular file operations
        try:
            if operation_type == "mount":
                root = agent_request.query.params.get("root", self.root_dir)
                result = self.sto_mount(
                    collection_name=collection_name,
                    root_dir=root
                )
            
            elif operation_type == "create_file":
                file_path = agent_request.query.params.get("file_path", None)
                result = self.sto_create_file(
                    file_path, collection_name
                )

            elif operation_type == "create_dir":
                dir_path = agent_request.query.params.get("dir_path", None)
                result = self.sto_create_directory(
                    dir_path=dir_path,
                    collection_name=collection_name
                )
                
            elif operation_type == "write":
                file_name = agent_request.query.params.get("file_name", None)
                file_path = agent_request.query.params.get("file_path", None)
                content = agent_request.query.params.get("content", None)
                result = self.sto_write(
                    file_name=file_name,
                    file_path=file_path,
                    content=content,
                    collection_name=collection_name
                )

            elif operation_type == "retrieve":
                query_text = agent_request.query.params.get("query_text", None)
                k = agent_request.query.params.get("k", "3")
                keywords = agent_request.query.params.get("keywords", None)
                result = self.sto_retrieve(
                    collection_name=collection_name,
                    query_text=query_text,
                    k=k,
                    keywords=keywords
                )
                
            elif operation_type == "rollback":
                file_path = agent_request.query.params.get("file_path", None)
                n = agent_request.query.params.get("n", "1")
                time = agent_request.query.params.get("time", None)
                result = self.sto_rollback(
                    file_path=file_path,
                    n=int(n),
                    time=time
                )

            elif operation_type == "share":
                file_path = agent_request.query.params.get("file_path", None)
                result = self.sto_share(
                    file_path=file_path,
                    collection_name=collection_name
                )
        
            else:
                result = f"Operation type: {operation_type} not supported"
        
        except Exception as e:
            result = f"Error handling file operation: {str(e)}"
        return result

    def sto_create_file(self, file_name: str, file_path: str, collection_name: str = None) -> bool:
        try:
            if file_path is None:
                file_path = os.path.join(self.root_dir, file_name)
            
            if not os.path.exists(file_path):
                with open(file_path, 'w') as f:
                    pass  # Create empty file
                
                if self.use_vector_db:
                    self.vector_db.update_document(file_path, "", collection_name)
                return "File has been created successfully at: " + file_path
            return "File already exists at: " + file_path
        
        except Exception as e:
            return f"Error creating file: {str(e)}"
            
    def sto_create_directory(self, dir_name: str, dir_path: str, collection_name: str = None) -> bool:
        try:
            if dir_path is None:
                dir_path = os.path.join(self.root_dir, dir_name)
            
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                # if self.use_vector_db:
                #     self.vector_db.create_directory(dir_name, collection_name)
                return "Directory has been created successfully at: " + dir_path
            return "Directory already exists at: " + dir_path
        
        except Exception as e:
            return f"Error creating directory: {str(e)}"
            
    def sto_mount(self, collection_name: str, root_dir: str) -> str:
        try:
            collection = self.vector_db.add_or_get_collection(collection_name)
            assert collection is not None, f"Collection {collection_name} not found"
            self.vector_db.build_database(root_dir)
            response = f"File system mounted successfully for agent: {collection_name}"
            return response
        
        except Exception as e:
            response = f"Error mounting file system: {str(e)}"
            return response
            
    def sto_write(self, file_name: str, file_path: str, content: str, collection_name: str = None) -> str:
        """Write to file with proper lock management."""
        if file_path is None:
            file_path = os.path.join(self.root_dir, file_name)
            
        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=10):  # Add timeout to prevent deadlocks
                try:
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    if self.use_vector_db:
                        self.vector_db.update_document(
                            file_path=file_path,
                            content=content
                        )
                    
                    return f"Content has been written to file: {file_path}"
                finally:
                    lock.release()  # Ensure lock is always released
            else:
                return f"Timeout waiting for lock on {file_path}"
        except Exception as e:
            return f"Error writing to file: {str(e)}"
            
    def sto_retrieve(self, collection_name: str, query_text: str, k: str = "3", keywords: str = None) -> list:
        try:
            collection = self.vector_db.add_or_get_collection(collection_name)
            return self.vector_db.retrieve(collection, query_text, k, keywords)
        
        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []
            
    def sto_rollback(self, file_path, n=1, time=None) -> bool:
        try:
            if not self.use_redis:
                return "Redis is not enabled. Please make sure the redis server has been installed and running."
            
            versions = self.get_file_history(file_path)
            
            if time:
                # Find version closest to specified time
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
                    result = self.restore_version(file_path, target_version)
                    if result:
                        return f"Successfully rolled back the file: {file_path} to its previous {n} version"
                    else:
                        return f"Failed to roll back the file: {file_path} to its previous {n} version"
            else:
                # Rollback n versions
                target_version = int(n)
                
                result = self.restore_version(file_path, target_version)
                if result:
                    return f"Successfully rolled back the file: {file_path} to its previous {n} version"
                else:
                    return f"Failed to roll back the file: {file_path} to its previous {n} version"
                
            return result
        
        except Exception as e:
            result = f"Error rolling back file: {str(e)}"
            return result
            
    def generate_share_link(self, file_path: str) -> str:
        """Generate a publicly accessible link for sharing a file.
        
        Args:
            file_path: Path to the file to be shared
            
        Returns:
            str: A public URL where the file can be accessed
        """
        try:
            # First check if we already have a valid share link in Redis
            if not self.use_redis:
                return "Redis is not enabled. Please make sure the redis server has been installed and running."
            
            file_hash = self.get_file_hash(file_path)
            share_key = f"share:link:{file_hash}"
            
            existing_share = self.redis_client.hgetall(share_key)
            if existing_share and datetime.fromisoformat(existing_share['expires_at']) > datetime.now():
                return existing_share['share_link']

            # If no valid existing share, create new one
            with open(file_path, 'rb') as f:
                # Option 1: Using transfer.sh
                response = requests.put(
                    f'https://transfer.sh/{file_hash}',
                    data=f.read(),
                    headers={'Max-Days': '7'}
                )
                share_link = response.text.strip()
                
                # Option 2: Using 0x0.st (alternative)
                # response = requests.post(
                #     'https://0x0.st',
                #     files={'file': f}
                # )
                # share_link = response.text.strip()

            # Store share info in Redis
            share_info = {
                "file_path": file_path,
                "share_link": share_link,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat(),
                "file_hash": file_hash
            }
            
            self.redis_client.hmset(share_key, share_info)
            self.redis_client.expire(share_key, 60 * 60 * 24 * 7)  # 7 days TTL

            return share_link

        except Exception as e:
            print(f"Error generating public share link: {str(e)}")
            return None

    def sto_share(self, file_path: str, collection_name: str = None) -> dict:
        """Share file with proper lock management."""
        lock = self.get_file_lock(file_path)
        try:
            if lock.acquire(timeout=10):  # Add timeout to prevent deadlocks
                try:
                    if not os.path.exists(file_path):
                        return {"error": "File not found"}
                        
                    share_link = self.generate_share_link(file_path)
                    if not share_link:
                        return {"error": "Failed to generate share link"}

                    return {
                        "file_name": os.path.basename(file_path),
                        "file_path": file_path,
                        "share_link": share_link,
                        "expires_in": "7 days",
                        "last_modified": datetime.fromtimestamp(
                            os.path.getmtime(file_path)
                        ).isoformat()
                    }
                finally:
                    lock.release()  # Ensure lock is always released
            else:
                return {"error": f"Timeout waiting for lock on {file_path}"}
        except Exception as e:
            return {"error": f"Error sharing file: {str(e)}"}

    def set_agent_permissions(self, agent_name: str, paths: List[str], operations: List[str]) -> None:
        """Set permissions for an agent.
        
        Args:
            agent_name: Name of the agent
            paths: List of paths the agent can access. Use "*" for all paths.
            operations: List of operations the agent can perform. Use "*" for all operations.
        """
        with self.permissions_lock:
            self.agent_permissions[agent_name] = {
                "paths": set(paths),
                "operations": set(operations)
            }
    
    def check_permission(self, agent_name: str, operation: str, path: Optional[str] = None) -> bool:
        """Check if an agent has permission to perform an operation on a path.
        
        Args:
            agent_name: Name of the agent
            operation: Operation to check (mount, create_file, write, retrieve, etc.)
            path: Path to check permission for
            
        Returns:
            bool: True if agent has permission, False otherwise
        """
        with self.permissions_lock:
            # If agent doesn't exist in permissions, deny access
            if agent_name not in self.agent_permissions:
                return False
                
            agent_perms = self.agent_permissions[agent_name]
            
            # Check operation permission
            if "*" not in agent_perms["operations"] and operation not in agent_perms["operations"]:
                return False
                
            # If no path is provided or operation doesn't require path check
            if path is None or operation in ["mount", "retrieve"]:
                return True
                
            # Check path permission
            if "*" in agent_perms["paths"]:
                return True
                
            # Check if the path or any parent directory is in the allowed paths
            path_parts = path.split(os.sep)
            for i in range(len(path_parts)):
                check_path = os.sep.join(path_parts[:i+1])
                if check_path in agent_perms["paths"]:
                    return True
                    
            return False

    # Add methods to manage permissions
    def grant_permission(self, admin_agent: str, target_agent: str, paths: List[str], operations: List[str]) -> str:
        """Grant permissions to an agent (requires admin privileges).
        
        Args:
            admin_agent: Name of the agent requesting the permission change
            target_agent: Name of the agent to grant permissions to
            paths: List of paths to grant access to
            operations: List of operations to grant
            
        Returns:
            str: Result message
        """
        if not self.check_permission(admin_agent, "grant_permission"):
            return f"Permission denied: Agent '{admin_agent}' does not have admin privileges"
            
        self.set_agent_permissions(target_agent, paths, operations)
        return f"Permissions granted to agent '{target_agent}'"
        
    def revoke_permission(self, admin_agent: str, target_agent: str) -> str:
        """Revoke all permissions from an agent (requires admin privileges).
        
        Args:
            admin_agent: Name of the agent requesting the permission change
            target_agent: Name of the agent to revoke permissions from
            
        Returns:
            str: Result message
        """
        if not self.check_permission(admin_agent, "revoke_permission"):
            return f"Permission denied: Agent '{admin_agent}' does not have admin privileges"
            
        with self.permissions_lock:
            if target_agent in self.agent_permissions:
                del self.agent_permissions[target_agent]
                return f"Permissions revoked from agent '{target_agent}'"
            else:
                return f"Agent '{target_agent}' has no permissions to revoke"
                
    def get_agent_permissions(self, admin_agent: str, target_agent: str = None) -> dict:
        """Get permissions for an agent or all agents (requires admin privileges).
        
        Args:
            admin_agent: Name of the agent requesting the permissions
            target_agent: Optional name of specific agent to get permissions for
            
        Returns:
            dict: Permissions information
        """
        if not self.check_permission(admin_agent, "get_permissions"):
            return {"error": f"Permission denied: Agent '{admin_agent}' does not have admin privileges"}
            
        with self.permissions_lock:
            if target_agent:
                if target_agent in self.agent_permissions:
                    perms = self.agent_permissions[target_agent]
                    return {
                        "agent": target_agent,
                        "paths": list(perms["paths"]),
                        "operations": list(perms["operations"])
                    }
                else:
                    return {"error": f"Agent '{target_agent}' not found"}
            else:
                # Return all permissions
                result = {}
                for agent, perms in self.agent_permissions.items():
                    result[agent] = {
                        "paths": list(perms["paths"]),
                        "operations": list(perms["operations"])
                    }
                return result

    def create_priority_group(self, group_name: str, admin_agent: str) -> str:
        """Create a new priority group with the specified admin as the first member.
        
        Args:
            group_name: Name of the new group
            admin_agent: Name of the agent creating the group (becomes group admin)
            
        Returns:
            str: Result message
        """
        with self.groups_lock:
            if group_name in self.priority_groups:
                return f"Group '{group_name}' already exists"
                
            # Create the group with admin as first member
            self.priority_groups[group_name] = {admin_agent}
            
            # Add group to agent's groups
            if admin_agent not in self.agent_groups:
                self.agent_groups[admin_agent] = set()
            self.agent_groups[admin_agent].add(group_name)
            
            return f"Priority group '{group_name}' created with '{admin_agent}' as admin"
    
    def add_agent_to_group(self, group_name: str, agent_name: str, admin_agent: str) -> str:
        """Add an agent to a priority group (requires group admin privileges).
        
        Args:
            group_name: Name of the group to add agent to
            agent_name: Name of the agent to add
            admin_agent: Name of the agent requesting the addition (must be in group)
            
        Returns:
            str: Result message
        """
        with self.groups_lock:
            # Check if group exists
            if group_name not in self.priority_groups:
                return f"Group '{group_name}' does not exist"
                
            # Check if admin is in the group
            if admin_agent not in self.priority_groups[group_name]:
                return f"Permission denied: Agent '{admin_agent}' is not a member of group '{group_name}'"
                
            # Add agent to group
            self.priority_groups[group_name].add(agent_name)
            
            # Add group to agent's groups
            if agent_name not in self.agent_groups:
                self.agent_groups[agent_name] = set()
            self.agent_groups[agent_name].add(group_name)
            
            return f"Agent '{agent_name}' added to group '{group_name}'"
    
    def remove_agent_from_group(self, group_name: str, agent_name: str, admin_agent: str) -> str:
        """Remove an agent from a priority group (requires group admin privileges).
        
        Args:
            group_name: Name of the group to remove agent from
            agent_name: Name of the agent to remove
            admin_agent: Name of the agent requesting the removal (must be in group)
            
        Returns:
            str: Result message
        """
        with self.groups_lock:
            # Check if group exists
            if group_name not in self.priority_groups:
                return f"Group '{group_name}' does not exist"
                
            # Check if admin is in the group
            if admin_agent not in self.priority_groups[group_name]:
                return f"Permission denied: Agent '{admin_agent}' is not a member of group '{group_name}'"
                
            # Check if agent is in the group
            if agent_name not in self.priority_groups[group_name]:
                return f"Agent '{agent_name}' is not a member of group '{group_name}'"
                
            # Remove agent from group
            self.priority_groups[group_name].remove(agent_name)
            
            # Remove group from agent's groups
            if agent_name in self.agent_groups and group_name in self.agent_groups[agent_name]:
                self.agent_groups[agent_name].remove(group_name)
                
            return f"Agent '{agent_name}' removed from group '{group_name}'"
    
    def get_agent_groups(self, agent_name: str) -> list:
        """Get all groups an agent belongs to.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            list: List of group names
        """
        with self.groups_lock:
            if agent_name not in self.agent_groups:
                return []
            return list(self.agent_groups[agent_name])
    
    def get_group_members(self, group_name: str, agent_name: str) -> dict:
        """Get all members of a group (requires group membership).
        
        Args:
            group_name: Name of the group
            agent_name: Name of the agent requesting the information (must be in group)
            
        Returns:
            dict: Group information including members
        """
        with self.groups_lock:
            # Check if group exists
            if group_name not in self.priority_groups:
                return {"error": f"Group '{group_name}' does not exist"}
                
            # Check if agent is in the group
            if agent_name not in self.priority_groups[group_name]:
                return {"error": f"Permission denied: Agent '{agent_name}' is not a member of group '{group_name}'"}
                
            return {
                "group": group_name,
                "members": list(self.priority_groups[group_name])
            }
    
    def check_group_access(self, requester_agent: str, target_agent: str) -> bool:
        """Check if requester agent has access to target agent's data through shared group membership.
        
        Args:
            requester_agent: Name of the agent requesting access
            target_agent: Name of the agent whose data is being accessed
            
        Returns:
            bool: True if agents share a group, False otherwise
        """
        # Admin has access to everything
        if requester_agent == "admin":
            return True
            
        # Self-access is always allowed
        if requester_agent == target_agent:
            return True
            
        with self.groups_lock:
            # If either agent is not in any groups, deny access
            if requester_agent not in self.agent_groups or target_agent not in self.agent_groups:
                return False
                
            # Check for shared group membership
            requester_groups = self.agent_groups[requester_agent]
            target_groups = self.agent_groups[target_agent]
            
            # If they share any group, allow access
            return bool(requester_groups.intersection(target_groups))

    def is_agent_registered(self, agent_name: str) -> bool:
        """Check if an agent is registered in the system.
        
        Args:
            agent_name: Name of the agent to check
            
        Returns:
            bool: True if agent is registered, False otherwise
        """
        # 检查 agent 是否在权限系统中注册
        with self.permissions_lock:
            if agent_name in self.agent_permissions:
                return True
        
        # 检查 agent 是否在任何优先级组中
        with self.groups_lock:
            if agent_name in self.agent_groups:
                return True
            
            # 检查所有组中是否包含该 agent
            for group_members in self.priority_groups.values():
                if agent_name in group_members:
                    return True
        
        # 如果是 admin，始终返回 True
        if agent_name == "admin":
            return True
        
        return False

    def register_agent(self, agent_name: str, admin_agent: str = None) -> str:
        """Register a new agent in the system.
        
        Args:
            agent_name: Name of the agent to register
            admin_agent: Optional name of admin agent registering this agent
            
        Returns:
            str: Result message
        """
        # 如果提供了 admin_agent，检查其权限
        if admin_agent and not self.check_permission(admin_agent, "register_agent"):
            return f"Permission denied: Agent '{admin_agent}' does not have permission to register new agents"
        
        # 检查 agent 是否已注册
        if self.is_agent_registered(agent_name):
            return f"Agent '{agent_name}' is already registered"
        
        # 注册 agent（设置基本权限）
        self.set_agent_permissions(agent_name, [self.root_dir], ["mount", "retrieve"])
        
        # 创建 agent 的默认组
        default_group_name = f"{agent_name}_group"
        self.create_priority_group(default_group_name, agent_name)
        
        return f"Agent '{agent_name}' registered successfully with default permissions"

    def get_agent_data_path(self, agent_name: str) -> str:
        """Get the data path for an agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            str: Path to agent's data directory
        """
        # 为每个 agent 创建专属数据目录
        agent_path = os.path.join(self.root_dir, "agent_data", agent_name)
        
        # 确保目录存在
        if not os.path.exists(agent_path):
            os.makedirs(agent_path, exist_ok=True)
        
        return agent_path

    def authorize_agent_access(self, owner_agent: str, target_agent: str) -> str:
        """Authorize another agent to access this agent's data.
        
        Args:
            owner_agent: Name of the agent granting access
            target_agent: Name of the agent receiving access
            
        Returns:
            str: Result message
        """
        # 检查两个 agent 是否都已注册
        if not self.is_agent_registered(owner_agent):
            return f"Error: Agent '{owner_agent}' is not registered"
        
        if not self.is_agent_registered(target_agent):
            return f"Error: Agent '{target_agent}' is not registered"
        
        # 获取 owner_agent 的默认组
        owner_groups = self.get_agent_groups(owner_agent)
        default_group = next((g for g in owner_groups if g.startswith(f"{owner_agent}_")), None)
        
        if not default_group:
            # 如果没有默认组，创建一个
            default_group = f"{owner_agent}_group"
            self.create_priority_group(default_group, owner_agent)
        
        # 将 target_agent 添加到 owner_agent 的组中
        result = self.add_agent_to_group(default_group, target_agent, owner_agent)
        
        if "added to group" in result:
            # 授予 target_agent 访问 owner_agent 数据的权限
            owner_path = self.get_agent_data_path(owner_agent)
            
            with self.permissions_lock:
                if target_agent in self.agent_permissions:
                    self.agent_permissions[target_agent]["paths"].add(owner_path)
                else:
                    self.set_agent_permissions(target_agent, [owner_path], ["retrieve"])
                
            return f"Agent '{target_agent}' authorized to access '{owner_agent}' data"
        
        return result

    def revoke_agent_access(self, owner_agent: str, target_agent: str) -> str:
        """Revoke another agent's access to this agent's data.
        
        Args:
            owner_agent: Name of the agent revoking access
            target_agent: Name of the agent losing access
            
        Returns:
            str: Result message
        """
        # 获取 owner_agent 的所有组
        owner_groups = self.get_agent_groups(owner_agent)
        
        # 从所有 owner_agent 的组中移除 target_agent
        results = []
        for group in owner_groups:
            if group.startswith(f"{owner_agent}_"):
                result = self.remove_agent_from_group(group, target_agent, owner_agent)
                results.append(result)
        
        # 移除 target_agent 对 owner_agent 数据路径的权限
        owner_path = self.get_agent_data_path(owner_agent)
        
        with self.permissions_lock:
            if target_agent in self.agent_permissions and owner_path in self.agent_permissions[target_agent]["paths"]:
                self.agent_permissions[target_agent]["paths"].remove(owner_path)
        
        if any("removed from group" in result for result in results):
            return f"Access for agent '{target_agent}' to '{owner_agent}' data has been revoked"
        
        return f"Agent '{target_agent}' did not have access to '{owner_agent}' data"
