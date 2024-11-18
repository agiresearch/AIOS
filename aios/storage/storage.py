import os

import pickle

import zlib

from .storage_classes.db_storage import ChromaDB

class StorageManager:
    def __init__(self, root_dir, use_vector_db=False):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)
        if use_vector_db:
            self.vector_db = ChromaDB()

    def address_request(self, agent_request):
        operation_type = agent_request.operation_type
        if operation_type == "create":
            self.sto_create(agent_request.agent_name)
        elif operation_type == "write":
            self.sto_write(agent_request.agent_name, s=agent_request.prompt)
        elif operation_type == "read":
            return self.sto_read(agent_request.agent_name)
        elif operation_type == "clear":
            self.sto_clear(agent_request.agent_name)
        elif operation_type == "retrieve":
            return self.sto_retrieve(
                agent_request.agent_name, query=agent_request.prompt
            )

    def sto_create(self, aname, aid=None, rid=None):
        file_path = os.path.join(
            self.storage_path, f"{aid}_{rid}.dat" if aid and rid else f"{aname}.dat"
        )

        if not os.path.exists(file_path):
            with open(file_path, "wb") as file:
                file.write(b"")
        if self.use_vector_db:
            self.vector_db.create_collection(f"{aid}_{rid}" if aid and rid else aname)

    def sto_read(self, aname, aid=None, rid=None):
        file_path = os.path.join(
            self.storage_path, f"{aid}_{rid}.dat" if aid and rid else f"{aname}.dat"
        )

        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                compressed_data = file.read()
                return (
                    pickle.loads(zlib.decompress(compressed_data))
                    if compressed_data
                    else None
                )
        return None

    def sto_write(self, aname, s, aid=None, rid=None):
        """Writes compressed data to a storage file and adds it to the vector database"""
        file_path = os.path.join(
            self.storage_path, f"{aid}_{rid}.dat" if aid and rid else f"{aname}.dat"
        )

        with open(file_path, "ab") as file:
            compressed_data = zlib.compress(pickle.dumps(s))
            file.write(compressed_data)
        if self.use_vector_db:
            self.vector_db.add(f"{aid}_{rid}" if aid and rid else aname, s)

    def sto_clear(self, aname, aid=None, rid=None):
        file_path = os.path.join(
            self.storage_path, f"{aid}_{rid}.dat" if aid and rid else f"{aname}.dat"
        )

        if os.path.exists(file_path):
            os.remove(file_path)
        if self.use_vector_db:
            self.vector_db.delete(f"{aid}_{rid}" if aid and rid else aname)

    def sto_retrieve(self, aname, query, aid=None, rid=None):
        if self.use_vector_db:
            return self.vector_db.retrieve(
                f"{aid}_{rid}" if aid and rid else aname, query
            )
        return None
