import asyncio
import os
from datetime import datetime
import logging
from typing import List
from .db_manager import DBManager
from .langchain_manager import LangChainManager
from .types import User, ImapAuth, State, SearchResult
from .mails import MailingManager

class MailSearcher:
    """Main class for email search functionality."""
    
    def __init__(self, persist_directory: str = None):
        """Initialize with empty references to components.
        
        Args:
            persist_directory: Directory to persist the vector store (None for in-memory)
        """
        logging.info("Creating MailSearcher instance")
        self.db_manager = None
        self.mailing_manager = None
        self.langchain_manager = None
        self.persist_directory = persist_directory
        
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
        
        # Initialize LangChain manager
        self.langchain_manager = LangChainManager(persist_directory=self.persist_directory)
        
        return True
        
    async def start(self):
        """Start the email syncing process in a non-blocking way."""
        logging.info("Starting email sync process")
        # Create a task that runs in the background
        asyncio.create_task(self.sync_emails())
        return True

    async def sync_emails(self, max_emails_to_sync: int = 10) -> None:
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
                
            # Add processed emails to vector store using LangChain
            self.langchain_manager.add_processed_mails(processed_mails)
            
            # Increment counter and log progress
            emails_synced += len(processed_mails)
            logging.info(f"Synced {len(processed_mails)} emails, total: {emails_synced}/{max_emails_to_sync}")
            
            # Check if we've reached the limit
            if emails_synced >= max_emails_to_sync:
                logging.info(f"Reached maximum of {max_emails_to_sync} emails, stopping sync")
                break
        
        logging.info(f"Email sync completed, processed {emails_synced} emails")

    def search(self, query: str, n_results: int = 5) -> List[SearchResult]:
        """Search emails based on query.
        
        Args:
            query: The search query
            n_results: Number of results to return
            
        Returns:
            List of SearchResult objects with their metadata and similarity scores
        """
        return self.langchain_manager.search(query, n_results)

    def get_state(self) -> State:
        """Get current state."""
        return self.db_manager.get_user().state