import os
import chromadb
from datetime import datetime
from llama_index.core import SimpleDirectoryReader

class ChromaDB:
    def __init__(self, mount_dir) -> None:
        super().__init__()
        self.mount_dir = mount_dir
        # self.build_database()

        self.client = chromadb.PersistentClient(self.mount_dir)
        # self.collection = self.add_or_get_collection(collection_name)
        
    def add_or_get_collection(self, collection_name):
        # collection_name = os.path.join(os.path.basename(self.mount_dir), collection_name)
        collection = self.client.get_or_create_collection(name=collection_name)
        return collection

    def build_database(self):
        for subdir, _, files in os.walk(self.mount_dir):
            for f in files:
                file_path = os.path.join(subdir, f)
                file_name = os.path.splitext(f)[0]
                if file_name == ".DS_Store":
                    continue
                self.update_document(file_path, file_name)

    def update_file(self, file_path: str, content: str, collection_name: str = None):
        try:
            if collection_name is None:
                collection_name = "terminal"
            
            collection = self.add_or_get_collection(collection_name)
            file_name = os.path.basename(file_path)
            
            metadata = {
                "file_path": file_path,
                "file_name": file_name,
                "last_modified": datetime.now().isoformat()
            }
            
            # Check if document exists
            existing = collection.get(ids=[file_name])
            
            if existing["ids"]:
                collection.update(
                    documents=[content],
                    ids=[file_name],
                    metadatas=[metadata]
                )
            else:
                collection.add(
                    documents=[content],
                    ids=[file_name],
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
        
        except Exception as e:
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
