from .types import Mail, ProcessedMail
import textwrap
from typing import List

class MailProcessor:
    """Processes raw emails into chunks for embedding."""
    def process_mail(self, mail: Mail) -> List[ProcessedMail]:
        """Split email body into 500-character chunks."""
        body = mail.body or ""
        # Minimal cleaning: just use the body as-is and split
        chunks = textwrap.wrap(body, 500)  # Split at 500 chars
        processed_mails = [
            ProcessedMail(
                mail_uid=mail.uid,
                chunk_index=i,
                text=chunk
            )
            for i, chunk in enumerate(chunks)
        ]
        return processed_mails if processed_mails else [ProcessedMail(mail.uid, 0, "")]