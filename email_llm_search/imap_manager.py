import aioimaplib
import email
from email.policy import default
from .types import Mail, ImapAuth
import os
from typing import List

class ImapManager:
    """Manages email fetching from Gmail via IMAP."""
    def __init__(self, auth: ImapAuth):
        self.auth = auth
        self.host = "imap.gmail.com"
        self.port = 993
        self.max_emails = int(os.getenv("MAX_EMAILS_TO_FETCH", "10"))  # Configurable limit

    async def fetch_emails(self) -> List[Mail]:
        """Fetch a limited number of recent emails asynchronously."""
        client = aioimaplib.IMAP4_SSL(host=self.host, port=self.port)
        await client.wait_hello_from_server()
        await client.login(self.auth.email, self.auth.password)
        await client.select("INBOX")
        _, data = await client.search("ALL")
        email_ids = data[0].split()[-self.max_emails:]  # Fetch last N emails
        emails = []
        for eid in email_ids:
            _, data = await client.fetch(eid, "(RFC822)")
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email, policy=default)
            mail = Mail(
                uid=eid.decode(),
                subject=msg["Subject"] or "",
                from_=msg["From"] or "",
                to=msg["To"] or "",
                date=msg["Date"] or "",
                body=self._get_email_body(msg)
            )
            emails.append(mail)
        await client.logout()
        return emails

    def _get_email_body(self, msg) -> str:
        """Extract plain text body from email."""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        return part.get_payload(decode=True).decode()
                    except:
                        return ""
        else:
            try:
                return msg.get_payload(decode=True).decode()
            except:
                return ""
        return ""