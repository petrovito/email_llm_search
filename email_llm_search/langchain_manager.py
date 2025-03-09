import os
import uuid
from typing import List, Dict, Any
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from .types import ProcessedMail, SearchResult

class LangChainManager:
    """Manages embeddings and vector database operations using LangChain."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", persist_directory: str = None, collection_name: str = None):
        """Initialize the LangChain manager.
        
        Args:
            model_name: The name of the embedding model to use
            persist_directory: Directory to persist the vector store (None for in-memory)
            collection_name: Name of the collection to use (None for a random name)
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.collection_name = collection_name or f"emails_{uuid.uuid4().hex[:8]}"
        
        # Initialize the embedding model
        model_kwargs = {'device': 'cpu'}
        encode_kwargs = {'normalize_embeddings': True}
        self.embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
            cache_folder=os.path.join("models", model_name)
        )
        
        # Initialize the vector store
        self.vector_store = self._initialize_vector_store()
        
        logging.info(f"Initialized LangChainManager with model {model_name} and collection {self.collection_name}")
    
    def _initialize_vector_store(self):
        """Initialize the vector store."""
        try:
            if self.persist_directory and os.path.exists(self.persist_directory):
                # Load existing vector store
                logging.info(f"Loading existing vector store from {self.persist_directory}")
                return Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                    collection_name=self.collection_name
                )
            else:
                # Create new vector store
                logging.info(f"Creating new vector store with collection {self.collection_name}")
                if self.persist_directory:
                    return Chroma(
                        persist_directory=self.persist_directory,
                        embedding_function=self.embeddings,
                        collection_name=self.collection_name
                    )
                else:
                    return Chroma(
                        embedding_function=self.embeddings,
                        collection_name=self.collection_name
                    )
        except Exception as e:
            logging.error(f"Error initializing vector store: {e}")
            # Fallback to in-memory store
            return Chroma(
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
    
    def add_processed_mails(self, processed_mails: List[ProcessedMail]) -> None:
        """Add processed emails to the vector store.
        
        Args:
            processed_mails: List of processed emails to add
        """
        if not processed_mails:
            return
        
        documents = []
        
        for processed_mail in processed_mails:
            for i, chunk in enumerate(processed_mail.chunks):
                # Create a document for each chunk
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "mail_uid": processed_mail.mail_uid,
                        "chunk_index": i
                    }
                )
                documents.append(doc)
        
        if documents:
            logging.info(f"Adding {len(documents)} documents to vector store")
            self.vector_store.add_documents(documents)
            
            # Persist if directory is specified
            if self.persist_directory:
                self.vector_store.persist()
    
    def search(self, query: str, n_results: int = 5) -> List[SearchResult]:
        """Search for similar documents in the vector store.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of SearchResult objects with their metadata and similarity scores
        """
        try:
            logging.info(f"Searching for: {query}")
            
            # Check if the collection is empty
            if self.vector_store._collection.count() == 0:
                return []
                
            results = self.vector_store.similarity_search_with_score(query, k=n_results)
            
            # Convert to SearchResult objects
            return [SearchResult.from_document(doc, score) for doc, score in results]
            
        except Exception as e:
            logging.error(f"Error searching vector store: {e}")
            return [] 