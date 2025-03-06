from typing import List, Dict, Any, Optional, Union
from sentence_transformers import SentenceTransformer
import nltk
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import chromadb
from chromadb.config import Settings
import pickle
from nltk.tokenize import word_tokenize
import os

def simple_tokenize(text):
    return word_tokenize(text)

class SimpleEmbeddingRetriever:
    """Simple retriever using sentence embeddings"""
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.documents = []
        self.embeddings = None
        
    def add_document(self, document: str):
        """Add a document to the retriever.
        
        Args:
            document: Text content to add
        """
        self.documents.append(document)
        # Update embeddings
        if len(self.documents) == 1:
            self.embeddings = self.model.encode([document])
        else:
            new_embedding = self.model.encode([document])
            self.embeddings = np.vstack([self.embeddings, new_embedding])
            
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of dictionaries containing document content and similarity score
        """
        if not self.documents:
            return []
            
        # Get query embedding
        query_embedding = self.model.encode([query])
        
        # Calculate cosine similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top k results
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            results.append({
                'content': self.documents[idx],
                'score': float(similarities[idx])
            })
            
        return results

class ChromaRetriever:
    """Vector database retrieval using ChromaDB"""
    def __init__(self, collection_name: str = "memories"):
        """Initialize ChromaDB retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection
        """
        self.client = chromadb.Client(Settings(allow_reset=True))
        self.collection = self.client.get_or_create_collection(name=collection_name)
        
    def add_document(self, document: str, metadata: Dict, doc_id: str):
        """Add a document to ChromaDB.
        
        Args:
            document: Text content to add
            metadata: Dictionary of metadata
            doc_id: Unique identifier for the document
        """
        # Convert lists to strings in metadata to comply with ChromaDB requirements
        processed_metadata = {}
        for key, value in metadata.items():
            if isinstance(value, list):
                processed_metadata[key] = ", ".join(value)
            else:
                processed_metadata[key] = value
                
        self.collection.add(
            documents=[document],
            metadatas=[processed_metadata],
            ids=[doc_id]
        )
        
    def delete_document(self, doc_id: str):
        """Delete a document from ChromaDB.
        
        Args:
            doc_id: ID of document to delete
        """
        self.collection.delete(ids=[doc_id])
        
    def search(self, query: str, k: int = 5):
        """Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of dicts with document text and metadata
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Convert string metadata back to lists where appropriate
        if 'metadatas' in results and results['metadatas']:
            for metadata in results['metadatas']:
                for key in ['keywords', 'tags']:
                    if key in metadata and isinstance(metadata[key], str):
                        metadata[key] = [item.strip() for item in metadata[key].split(',')]
                        
        return results
