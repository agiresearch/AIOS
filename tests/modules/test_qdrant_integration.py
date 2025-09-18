import unittest
import os
import tempfile
import uuid
import hashlib

os.environ["VECTOR_DB_BACKEND"] = "qdrant"
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6333"
os.environ["QDRANT_EMBEDDING_MODEL"] = "sentence-transformers/all-MiniLM-L6-v2"

from aios.memory.retrievers import QdrantRetriever
from aios.storage.filesystem.vector_db import QdrantDB


class TestQdrantIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(host="localhost", port=6333)
            client.get_collections()
        except Exception as e:
            raise unittest.SkipTest(f"Qdrant is not available: {e}")

    def setUp(self):
        self.test_collection = f"integration_test_{uuid.uuid4().hex[:8]}"
        self.temp_dir = tempfile.mkdtemp()

        self.retriever = QdrantRetriever(collection_name=self.test_collection)
        self.vector_db = QdrantDB(mount_dir=self.temp_dir)

    def tearDown(self):
        try:
            from qdrant_client import QdrantClient

            client = QdrantClient(host="localhost", port=6333)
            if client.collection_exists(self.test_collection):
                client.delete_collection(self.test_collection)
        except Exception:
            pass

    def test_retriever_basic_operations(self):
        test_documents = [
            "Machine learning is a subset of artificial intelligence",
            "Python is a popular programming language for data science",
            "Vector databases are used for similarity search and retrieval",
        ]

        for i, doc in enumerate(test_documents):
            self.retriever.add_document(doc, {"index": i, "type": "test"}, str(i))

        results = self.retriever.search("artificial intelligence", k=2)
        self.assertGreaterEqual(len(results["documents"]), 1)
        self.assertIn("documents", results)
        self.assertIn("metadatas", results)
        self.assertIn("ids", results)

        self.retriever.delete_document("1")
        results = self.retriever.search("test", k=5)
        doc_ids = [id for id in results["ids"]]
        self.assertNotIn("1", doc_ids)

    def test_vector_db_basic_operations(self):
        self.vector_db.add_or_get_collection(self.test_collection)
        file_path = "/test/document.txt"
        content = "Test document content for vector database operations"

        self.vector_db.update_document(
            file_path=file_path,
            file_content=content,
            collection_name=self.test_collection,
        )

        results = self.vector_db.retrieve(self.test_collection, "test document")
        self.assertGreater(len(results), 0)
        self.assertIn(content, results[0]["document_summary"])

        self.vector_db.delete_document(file_path, self.test_collection)
        results = self.vector_db.retrieve(self.test_collection, "deleted")
        for result in results:
            self.assertNotIn("deleted", result["document_summary"].lower())

    def test_cross_module_data_flow(self):
        test_doc = "Integration test document for cross-module data flow"
        file_path = "/test/integration_doc.txt"

        self.vector_db.add_or_get_collection(self.test_collection)
        self.vector_db.update_document(
            file_path=file_path,
            file_content=test_doc,
            collection_name=self.test_collection,
        )

        results = self.retriever.search(test_doc, k=1)

        self.assertGreaterEqual(len(results["documents"]), 1)
        self.assertIn("documents", results)
        self.assertIn("metadatas", results)
        self.assertIn("ids", results)

    def test_collection_management_across_modules(self):
        retriever_collection = f"retriever_{uuid.uuid4().hex[:8]}"
        retriever = QdrantRetriever(collection_name=retriever_collection)

        vector_db_collection = f"vector_db_{uuid.uuid4().hex[:8]}"
        self.vector_db.add_or_get_collection(vector_db_collection)

        from qdrant_client import QdrantClient

        client = QdrantClient(host="localhost", port=6333)

        self.assertTrue(client.collection_exists(retriever_collection))
        self.assertTrue(client.collection_exists(vector_db_collection))

        try:
            client.delete_collection(retriever_collection)
            client.delete_collection(vector_db_collection)
        except Exception:
            pass

    def test_factory_function_integration(self):
        os.environ["VECTOR_DB_BACKEND"] = "qdrant"

        import sys

        if "aios.storage.filesystem.vector_db" in sys.modules:
            del sys.modules["aios.storage.filesystem.vector_db"]

        from aios.storage.filesystem.vector_db import get_vector_db

        vector_db = get_vector_db(self.temp_dir)

        self.assertEqual(type(vector_db).__name__, "QdrantDB")
        self.assertEqual(vector_db.mount_dir, self.temp_dir)


if __name__ == "__main__":
    unittest.main()
