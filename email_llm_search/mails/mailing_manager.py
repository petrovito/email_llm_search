import logging
from typing import List, Optional, Set
from datetime import datetime
from .imap_manager import ImapManager
from .mail_processor import MailProcessor
from .types import MailingStatus
from ..types import Mail, ImapAuth, ProcessedMail

class MailingManager:
    """Manages email fetching, processing, and synchronization state."""
    
    def __init__(self, auth: ImapAuth):
        self.imap_manager = ImapManager(auth)
        self.mail_processor = MailProcessor()
        self._status = MailingStatus(total_emails=0, synced_emails=0)
        self._synced_ids = set()  # Keep track of which emails we've processed
        
    async def initialize(self) -> bool:
        """Initialize the mailing manager and test connection."""
        try:
            success = await self.imap_manager.test_login()
            if success:
                # Get initial mailbox status
                total = await self.imap_manager.get_total_email_count()
                self._status = MailingStatus(
                    total_emails=total,
                    synced_emails=0,
                    last_sync_time=None,
                    is_syncing=False
                )
            return success
        except Exception as e:
            logging.error(f"Failed to initialize mailing manager: {e}")
            self._status.error = str(e)
            return False

    async def get_processed_batch(self, batch_size: int = 10) -> List[ProcessedMail]:
        """Get a batch of unprocessed emails, process them, and mark as synced."""
        try:
            self._status.is_syncing = True
            
            # Get unprocessed emails
            emails = await self.imap_manager.fetch_emails(
                max_emails=batch_size,
                exclude_ids=self._synced_ids
            )
            
            if not emails:
                return []
            
            # Process each email
            processed_mails = []
            
            for email in emails:
                processed = await self.mail_processor.process_mail(email)
                if processed.chunks:
                    processed_mails.append(processed)
                    self._synced_ids.add(email.uid)
            
            self._status.synced_emails = len(self._synced_ids)
            self._status.last_sync_time = datetime.now()
            
            return processed_mails
            
        except Exception as e:
            logging.error(f"Error processing mail batch: {e}")
            self._status.error = str(e)
            return []
        finally:
            self._status.is_syncing = False

    async def get_mail_by_id(self, mail_id: str) -> Optional[Mail]:
        """Retrieve a specific email by its ID."""
        try:
            return await self.imap_manager.fetch_email_by_id(mail_id)
        except Exception as e:
            logging.error(f"Error fetching mail {mail_id}: {e}")
            return None

    def get_status(self) -> MailingStatus:
        """Get current mailing system status."""
        return self._status 