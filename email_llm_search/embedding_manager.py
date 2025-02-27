from sentence_transformers import SentenceTransformer
import os
from typing import List

class EmbeddingManager:
    """Manages the SentenceTransformer model and embeddings."""
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_path = os.path.join("models", model_name)
        if not os.path.exists(self.model_path):
            self.model = SentenceTransformer(model_name)
            self.model.save(self.model_path)
        else:
            self.model = SentenceTransformer(self.model_path)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of text chunks."""
        return self.model.encode(texts, convert_to_tensor=False).tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a single user query."""
        return self.model.encode([query], convert_to_tensor=False)[0].tolist()