import asyncio
import os
from datetime import datetime
import logging
from .db_manager import DBManager
from .imap_manager import ImapManager
from .mail_processor import MailProcessor
from .embedding_manager import EmbeddingManager
from .vector_db_manager import VectorDBManager
from .types import User, ImapAuth, State

class MailSearcherContext:
    """Context manager for email search app components."""
    async def __aenter__(self):
        logging.info("Initializing MailSearcherContext")
        self.db_manager = DBManager()
        user = self.db_manager.get_user()
        if user is None:
            # First-time run: fetch auth from env variables
            email = os.getenv("IMAP_EMAIL")
            password = os.getenv("IMAP_PASSWORD")
            if not email or not password:
                logging.error("IMAP_EMAIL and IMAP_PASSWORD must be set")
                print("Error: IMAP_EMAIL and IMAP_PASSWORD must be set in environment variables")
                exit(1)
            auth = ImapAuth(email=email, password=password)
            imap_manager = ImapManager(auth)
            try:
                await imap_manager.fetch_emails()  # Test login
            except Exception as e:
                logging.error(f"IMAP login failed: {e}")
                print(f"Error: IMAP login failed: {e}")
                exit(1)
            user = User(auth=auth, state=State())
            self.db_manager.set_user(user)

        self.imap_manager = ImapManager(user.auth)
        self.mail_processor = MailProcessor()
        self.embedding_manager = EmbeddingManager()
        self.vector_db_manager = VectorDBManager()
        await self.sync_emails()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        logging.info("Exiting MailSearcherContext")
        # No cleanup needed for in-memory resources

    async def sync_emails(self):
        """Sync emails from IMAP to vector database."""
        user = self.db_manager.get_user()
        user.state.sync_status = "syncing"
        self.db_manager.update_state(user.state)
        logging.info("Starting email sync")
        try:
            emails = await self.imap_manager.fetch_emails()
            for email in emails:
                processed_mails = self.mail_processor.process_mail(email)
                texts = [pm.text for pm in processed_mails]
                embeddings = self.embedding_manager.embed_texts(texts)
                ids = [f"{email.uid}_{i}" for i in range(len(processed_mails))]
                metadatas = [{
                    "mail_uid": email.uid,
                    "chunk_index": i,
                    "subject": email.subject,
                    "from": email.from_,
                    "to": email.to,
                    "date": email.date,
                    "text": pm.text
                } for i, pm in enumerate(processed_mails)]
                self.vector_db_manager.add_embeddings(embeddings, metadatas, ids)
            user.state.last_sync_time = datetime.now().isoformat()
            user.state.sync_status = "idle"
            logging.info("Email sync completed")
        except Exception as e:
            user.state.sync_status = "error"
            logging.error(f"Sync failed: {e}")
            raise
        finally:
            self.db_manager.update_state(user.state)

    def search(self, query: str, n_results: int = 5) -> dict:
        """Search emails based on query."""
        query_embedding = self.embedding_manager.embed_query(query)
        return self.vector_db_manager.search(query_embedding, n_results)

    def get_state(self) -> State:
        """Get current state."""
        return self.db_manager.get_user().state