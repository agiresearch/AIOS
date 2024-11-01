# TODO: Not implemented
# Storing to databases has not been implemented yet

from aios.storage.base import BaseStorage

import zlib
import pickle
import os

class StorageManager:
    def __init__(self, storage_path="persistent_storage", vector_db=None):
        self.storage_path = storage_path
        os.makedirs(self.storage_path, exist_ok=True)
        self.vector_db = vector_db  # Reference to the ChromaDB instance

    def sto_create(self, aname):
        """Creates a new storage file and initializes a collection in vector_db for the agent."""
        file_path = os.path.join(self.storage_path, f"{aname}.dat")
        if not os.path.exists(file_path):
            with open(file_path, "wb") as file:
                file.write(b"")
        # Create a collection in the vector database for this agent
        if self.vector_db:
            self.vector_db.create_collection(aname)

    def sto_read(self, aname):
        """Reads and decompresses data for a specific agent from the physical storage file."""
        file_path = os.path.join(self.storage_path, f"{aname}.dat")
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                compressed_data = file.read()
                return pickle.loads(zlib.decompress(compressed_data)) if compressed_data else None
        return None

    def sto_write(self, aname, s):
        """Writes data both to a file and to the vector database."""
        # Write data to physical file storage
        file_path = os.path.join(self.storage_path, f"{aname}.dat")
        with open(file_path, "ab") as file:  # Append mode
            compressed_data = zlib.compress(pickle.dumps(s))
            file.write(compressed_data)
        
        # Append data to the vector database, if available
        if self.vector_db:
            self.vector_db.add(aname, s)  # Assuming vector_db.add method supports appending data by agent name

    def sto_clear(self, aname):
        """Clears the physical file storage and deletes the vector database collection for an agent."""
        file_path = os.path.join(self.storage_path, f"{aname}.dat")
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Clear data from vector database if available
        if self.vector_db:
            self.vector_db.delete(aname)

    def sto_retrieve(self, aname, query):
        """Retrieves data from the vector database based on agent name and a query."""
        if self.vector_db:
            return self.vector_db.retrieve(aname, query)
        return None

