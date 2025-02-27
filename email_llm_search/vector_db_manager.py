import chromadb
from chromadb.config import Settings
from typing import List

class VectorDBManager:
    """Manages an in-memory Chroma vector database."""
    def __init__(self):
        self.client = chromadb.Client(Settings(is_persistent=False))  # In-memory only
        self.collection = self.client.create_collection("emails")

    def add_embeddings(self, embeddings: List[List[float]], metadatas: List[dict], ids: List[str]):
        """Add email embeddings to the vector database."""
        self.collection.add(embeddings=embeddings, metadatas=metadatas, ids=ids)

    def search(self, query_embedding: List[float], n_results: int = 5) -> dict:
        """Search for top N similar email chunks."""
        return self.collection.query(query_embeddings=[query_embedding], n_results=n_results)