import asyncio
import os
from datetime import datetime
import logging
from .db_manager import DBManager
from .embedding_manager import EmbeddingManager
from .vector_db_manager import VectorDBManager
from .types import User, ImapAuth, State
from .mails import MailingManager

class MailSearcher:
    """Main class for email search functionality."""
    
    def __init__(self):
        """Initialize with empty references to components."""
        logging.info("Creating MailSearcher instance")
        self.db_manager = None
        self.mailing_manager = None
        self.embedding_manager = None
        self.vector_db_manager = None
        
    async def initialize(self):
        """Initialize all components and connections."""
        logging.info("Initializing MailSearcher components")
        
        # Initialize database manager
        self.db_manager = DBManager()
        user = self.db_manager.get_user()
        
        if user is None:
            # First-time run: fetch auth from env variables
            email = os.getenv("IMAP_EMAIL")
            password = os.getenv("IMAP_PASSWORD")
            if not email or not password:
                logging.error("IMAP_EMAIL and IMAP_PASSWORD must be set")
                print("Error: IMAP_EMAIL and IMAP_PASSWORD must be set in environment variables")
                return False
            
            auth = ImapAuth(email=email, password=password)
            user = User(auth=auth, state=State())
            self.db_manager.set_user(user)
        
        # Initialize mailing manager
        self.mailing_manager = MailingManager(user.auth)
        if not await self.mailing_manager.initialize():
            logging.error("Failed to initialize mailing manager")
            return False
        
        # Initialize other components
        self.embedding_manager = EmbeddingManager()
        self.vector_db_manager = VectorDBManager()
        
        return True
        
    async def start(self):
        """Start the email syncing process in a non-blocking way."""
        logging.info("Starting email sync process")
        # Create a task that runs in the background
        asyncio.create_task(self.sync_emails())
        return True

    async def sync_emails(self, max_emails_to_sync: int = 3) -> None:
        """Synchronize emails from IMAP server to vector store.
        
        Args:
            max_emails_to_sync: Maximum number of emails to sync before stopping (for testing)
        """
        emails_synced = 0
        logging.info(f"Starting email sync, will process up to {max_emails_to_sync} emails")
        
        while emails_synced < max_emails_to_sync:
            processed_mails = await self.mailing_manager.get_processed_batch()
            if not processed_mails:
                logging.info("No more emails to process")
                break
                
            for processed_mail in processed_mails:
                # Skip emails with no chunks
                if not processed_mail.chunks:
                    continue
                    
                # Generate embeddings for all chunks in a single batch
                chunks = processed_mail.chunks
                embeddings = self.embedding_manager.embed_texts(chunks)
                
                # Skip if no embeddings were generated
                if not embeddings:
                    continue
                
                # Create metadata for each chunk
                metadatas = [{
                    "mail_uid": processed_mail.mail_uid,
                    "chunk_index": i,
                    "text": chunk
                } for i, chunk in enumerate(chunks)]
                
                # Generate unique IDs for each chunk
                ids = [f"{processed_mail.mail_uid}_{i}" for i in range(len(chunks))]
                
                # Add to vector store
                self.vector_db_manager.add_embeddings(
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                
                # Increment counter and log progress
                emails_synced += 1
                logging.info(f"Synced email {emails_synced}/{max_emails_to_sync}")
                
                # Check if we've reached the limit
                if emails_synced >= max_emails_to_sync:
                    logging.info(f"Reached maximum of {max_emails_to_sync} emails, stopping sync")
                    break
        
        logging.info(f"Email sync completed, processed {emails_synced} emails")

    def search(self, query: str, n_results: int = 5) -> dict:
        """Search emails based on query."""
        query_embedding = self.embedding_manager.embed_query(query)
        return self.vector_db_manager.search(query_embedding, n_results)

    def get_state(self) -> State:
        """Get current state."""
        return self.db_manager.get_user().state