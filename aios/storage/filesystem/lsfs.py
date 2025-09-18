import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import redis
import json
from datetime import datetime, timedelta
import hashlib
import threading
import requests

from .vector_db import get_vector_db
from aios.config.config_manager import config as global_config

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
        global_config.get_storage_config() or {}
        self.vector_db = get_vector_db(mount_dir=self.root_dir)

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

        if operation_type in ["create_file", "write", "rollback", "share"]:
            agent_request.query.params.get("file_path", None)
        elif operation_type == "create_dir":
            agent_request.query.params.get("dir_path", None)

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
                dir_name = agent_request.query.params.get("dir_name", None)
                result = self.sto_create_directory(
                    dir_name=dir_name,
                    dir_path=dir_path,
                    collection_name=collection_name
                )

            elif operation_type == "write":
                file_name = agent_request.query.params.get("file_name", None)
                file_path = agent_request.query.params.get("file_path", None)
                content = agent_request.query.params.get("content", None)
                # breakpoint()
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
                with open(file_path, 'w'):
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
