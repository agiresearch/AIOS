# This file will be an implementation of the shared memory mechanism for
# multi-agent systems

from aios.memory.base import BaseMemory
from threading import Lock
import pickle
import os

class SharedMemory(BaseMemory):
    def __init__(self, storage_path="shared_memory"):
        """Initialize shared memory
        
        Args:
            storage_path: Path for storing shared memory data
        """
        self.storage_path = storage_path
        self._memory = {}  # Dictionary for memory data
        self._lock = Lock()  # Thread lock for synchronization
        
        # Create storage directory if not exists
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
            
    def save(self, key, value, agent_id=None):
        """Save data to shared memory
        
        Args:
            key: Key for the data
            value: Data to be saved
            agent_id: Optional agent identifier
        """
        with self._lock:
            # Use agent_id as namespace if specified
            if agent_id:
                if agent_id not in self._memory:
                    self._memory[agent_id] = {}
                self._memory[agent_id][key] = value
            else:
                self._memory[key] = value
                
            # Persist to disk
            self._save_to_disk()

    def load(self, key, agent_id=None):
        """Load data from shared memory
        
        Args:
            key: Key of data to load
            agent_id: Optional agent identifier
            
        Returns:
            Loaded data, or None if not exists
        """
        with self._lock:
            # Load from disk if file exists
            self._load_from_disk()
            
            try:
                if agent_id:
                    return self._memory.get(agent_id, {}).get(key)
                return self._memory.get(key)
            except KeyError:
                return None
                
    def _save_to_disk(self):
        """Persist memory data to disk"""
        file_path = os.path.join(self.storage_path, "shared_memory.pkl")
        with open(file_path, "wb") as f:
            pickle.dump(self._memory, f)
            
    def _load_from_disk(self):
        """Load data from disk to memory"""
        file_path = os.path.join(self.storage_path, "shared_memory.pkl")
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                self._memory = pickle.load(f)
                
    def clear(self, agent_id=None):
        """Clear shared memory data
        
        Args:
            agent_id: Optional agent identifier, if specified only clear data for this agent
        """
        with self._lock:
            if agent_id:
                self._memory.pop(agent_id, None)
            else:
                self._memory.clear()
            self._save_to_disk()
            
    def get_all(self, agent_id=None):
        """Get all shared memory data
        
        Args:
            agent_id: Optional agent identifier, if specified only return data for this agent
            
        Returns:
            Dictionary containing all data
        """
        with self._lock:
            self._load_from_disk()
            if agent_id:
                return self._memory.get(agent_id, {})
            return self._memory
