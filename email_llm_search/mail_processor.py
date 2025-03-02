from .types import Mail, ProcessedMail
import textwrap
from typing import List
import logging

class MailProcessor:
    """Processes raw emails into chunks for embedding."""
    async def process_mail(self, mail: Mail) -> ProcessedMail:
        """Process a mail into chunks ready for embedding."""
        body = mail.body or ""
        # Minimal cleaning: just use the body as-is and split
        chunks = self._split_text(body)
        
        # Add logging
        logging.info(f"Processing email: {mail.uid}, subject: {mail.subject}")
        logging.info(f"Email body length: {len(mail.body)}")
        
        # After processing
        logging.info(f"Generated {len(chunks)} chunks for email {mail.uid}")
        
        # Return a single ProcessedMail with all chunks
        return ProcessedMail(
            mail_uid=mail.uid,
            chunks=chunks
        )

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks of appropriate size for embedding."""
        chunks = textwrap.wrap(text, 500)  # Split at 500 chars
        return chunks