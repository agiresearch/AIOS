import os
import chromadb
from datetime import datetime
from llama_index.core import SimpleDirectoryReader
import hashlib
from qdrant_client import QdrantClient, models
from aios.config.config_manager import config as global_config
import uuid

class ChromaDB:
    def __init__(self, mount_dir) -> None:
        super().__init__()
        self.mount_dir = mount_dir
        # self.build_database()

        self.client = chromadb.PersistentClient(self.mount_dir)
        # self.collection = self.add_or_get_collection(collection_name)

    def add_or_get_collection(self, collection_name):
        # collection_name = os.path.join(os.path.basename(self.mount_dir), collection_name)
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            collection = self.client.create_collection(name=collection_name)

        return collection

    def build_database(self, root_dir):
        # Check if database already exists
        # breakpoint()
        for subdir, _, files in os.walk(root_dir):
            for f in files:
                if f.endswith(".bin"):
                    result = "Database already mounted with bin files"
                    return result

        for subdir, _, files in os.walk(root_dir):
            for f in files:
                if f.endswith(".DS_Store") or f.endswith(".bin") or f.endswith("chroma.sqlite3"):
                    continue

                file_path = os.path.join(subdir, f)

                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                content = " ".join(doc.text for doc in documents)

                self.update_document(
                    file_path=file_path,
                    file_content=content
                )


        result = f"Database built with {len(files)} files"
        return result

    def update_document(self, file_path: str, file_content: str, collection_name: str = "terminal"):
        try:
            collection = self.add_or_get_collection(collection_name)

            file_name = os.path.basename(file_path)

            # Generate hash code from file path
            file_hash = hashlib.md5(file_path.encode()).hexdigest()

            metadata = {
                "file_path": file_path,
                "file_name": file_name,
                "last_modified": datetime.now().isoformat()
            }
            # Check if document exists
            existing = collection.get(ids=[file_hash])

            if existing["ids"]:
                collection.update(
                    documents=[file_content],
                    ids=[file_hash],
                    metadatas=[metadata]
                )
            else:
                collection.add(
                    documents=[file_content],
                    ids=[file_hash],
                    metadatas=[metadata]
                )

            return True

        except Exception as e:
            print(f"Error updating document in vector DB: {str(e)}")
            return False

    def delete_document(self, file_path: str, collection_name: str = None):
        try:
            if collection_name is None:
                collection_name = "terminal"
            collection = self.add_or_get_collection(collection_name)
            file_name = os.path.basename(file_path)

            existing = collection.get(ids=[file_name])
            if existing["ids"]:
                collection.delete(ids=[file_name])
                return True
            return False

        except Exception as e:
            print(f"Error deleting document from vector DB: {str(e)}")
            return False

    def retrieve(self, collection, query_text, k=3, keywords=None):
        try:
            # If keywords provided, add them to query
            if keywords:
                query_text = f"{query_text} {keywords}"

            results = collection.query(
                query_texts=[query_text],
                n_results=int(k)
            )

            documents = results["documents"][0]
            metadatas = results["metadatas"][0]
            # distances = results["distances"][0] if "distances" in results else None

            organized_results = []
            for i, doc in enumerate(documents):
                result = {
                    "document_summary": doc[:2000],  # Limit summary length
                    "metadata": metadatas[i],
                }
                # if distances:
                #     result["relevance_score"] = 1 - (distances[i] / max(distances))  # Normalize score
                organized_results.append(result)

            return organized_results

        except Exception as e:
            print(f"Error retrieving documents: {str(e)}")
            return []

    def create_directory(self, dir_name: str, collection_name: str = None):
        try:
            if collection_name is None:
                collection_name = "terminal"

            collection = self.add_or_get_collection(collection_name)

            metadata = {
                "type": "directory",
                "created_at": datetime.now().isoformat()
            }

            collection.add(
                documents=[f"Directory: {dir_name}"],
                ids=[f"dir_{dir_name}"],
                metadatas=[metadata]
            )
            return True

        except Exception:
            return False

    def link_document(self, file_path: str, collection_name: str = None):
        try:
            if collection_name is None:
                collection_name = "default"

            collection = self.add_or_get_collection(collection_name)
            file_name = os.path.basename(file_path)

            existing = collection.get(ids=[file_name])
            if existing["ids"]:
                return {
                    "file_name": file_name,
                    "file_path": file_path,
                    "collection": collection_name,
                    "metadata": existing["metadatas"][0]
                }
            return None
        except Exception as e:
            print(f"Error generating document link: {str(e)}")
            return None


class QdrantDB:
    def __init__(self, mount_dir) -> None:
        super().__init__()
        self.mount_dir = mount_dir
        storage_cfg = global_config.get_storage_config() or {}
        host = storage_cfg.get("qdrant_host", os.environ.get("QDRANT_HOST", "localhost"))
        port = int(storage_cfg.get("qdrant_port", os.environ.get("QDRANT_PORT", 6333)))
        api_key = storage_cfg.get("qdrant_api_key", os.environ.get("QDRANT_API_KEY"))
        self.client = QdrantClient(host=host, port=port, api_key=api_key or None)
        self.model_name = storage_cfg.get("qdrant_model_name") or os.environ.get("QDRANT_EMBEDDING_MODEL", 'sentence-transformers/all-MiniLM-L6-v2')

    def add_or_get_collection(self, collection_name):
        if not self.client.collection_exists(collection_name):
            vector_size = self.client.get_embedding_size(self.model_name)
            self.client.create_collection(
                collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
            )
        return collection_name

    def build_database(self, root_dir):
        file_count = 0
        for subdir, _, files in os.walk(root_dir):
            for f in files:
                if f.endswith(".DS_Store") or f.endswith(".bin") or f.endswith("chroma.sqlite3"):
                    continue
                file_path = os.path.join(subdir, f)
                documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
                content = " ".join(doc.text for doc in documents)
                self.update_document(file_path=file_path, file_content=content)
                file_count += 1
        result = f"Database built with {file_count} files"
        return result

    def update_document(self, file_path: str, file_content: str, collection_name: str = "terminal"):
        try:
            self.add_or_get_collection(collection_name)
            file_name = os.path.basename(file_path)
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            payload = {
                "file_path": file_path,
                "file_name": file_name,
                "last_modified": datetime.now().isoformat(),
                "document_summary": file_content[:2000],
            }
            # Deterministic UUIDv5 for Qdrant point id
            qdrant_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file_hash))
            self.client.upload_collection(
                collection_name=collection_name,
                vectors=[models.Document(text=file_content, model=self.model_name)],
                ids=[qdrant_id],
                payload=[payload],
            )
            return True
        except Exception as e:
            print(f"Error updating document in Qdrant: {str(e)}")
            return False

    def delete_document(self, file_path: str, collection_name: str):
        try:
            file_hash = hashlib.md5(file_path.encode()).hexdigest()
            qdrant_id = str(uuid.uuid5(uuid.NAMESPACE_URL, file_hash))
            self.add_or_get_collection(collection_name)
            self.client.delete(
                collection_name=collection_name,
                points_selector=[qdrant_id],
            )
            return True
        except Exception as e:
            print(f"Error deleting document from Qdrant: {str(e)}")
            return False

    def retrieve(self, collection, query_text, k=3, keywords=None):
        try:
            collection_name = collection if isinstance(collection, str) else "terminal"
            if keywords:
                query_text = f"{query_text} {keywords}"
            results = self.client.query_points(
                collection_name=collection_name,
                query=models.Document(text=query_text, model=self.model_name),
                limit=int(k),
            ).points
            organized_results = []
            for r in results:
                payload = r.payload or {}
                organized_results.append({
                    "document_summary": payload.get("document_summary", ""),
                    "metadata": {
                        "file_path": payload.get("file_path"),
                        "file_name": payload.get("file_name"),
                        "last_modified": payload.get("last_modified"),
                    },
                })
            return organized_results
        except Exception as e:
            print(f"Error retrieving documents from Qdrant: {str(e)}")
            return []

    def create_directory(self, dir_name: str, collection_name: str = None):
        # Not applicable for Qdrant, noop
        return False

    def link_document(self, file_path: str, collection_name: str = None):
        # Can be implemented if needed; return None for now
        return None


def get_vector_db(mount_dir):
    storage_cfg = global_config.get_storage_config() or {}
    backend = (os.environ.get("VECTOR_DB_BACKEND") or storage_cfg.get("vector_db_backend") or "chroma").lower()
    if backend == "qdrant":
        return QdrantDB(mount_dir=mount_dir)
    return ChromaDB(mount_dir=mount_dir)
