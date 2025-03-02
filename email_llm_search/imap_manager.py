import imaplib
import email
from email.policy import default
from .types import Mail, ImapAuth
import os
from typing import List
import ssl
import asyncio
from concurrent.futures import ThreadPoolExecutor

class ImapManager:
    """Manages email fetching from Gmail via IMAP using the standard imaplib."""
    def __init__(self, auth: ImapAuth):
        self.auth = auth
        self.host = "imap.gmail.com"
        self.port = 993
        self.max_emails = int(os.getenv("MAX_EMAILS_TO_FETCH", "1"))  # Configurable limit
        self._executor = ThreadPoolExecutor(max_workers=1)

    async def test_login(self) -> bool:
        """Test IMAP login without fetching emails."""
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._test_login_sync
        )
    
    def _test_login_sync(self) -> bool:
        """Synchronous implementation of login testing."""
        context = ssl.create_default_context()
        client = imaplib.IMAP4_SSL(self.host, self.port, ssl_context=context)
        
        try:
            # Try to login
            client.login(self.auth.email, self.auth.password)
            
            # If login succeeds, send a NOOP command to verify connection
            status, _ = client.noop()
            return status == 'OK'
            
        except Exception as e:
            print(f"Login test failed: {e}")
            return False
            
        finally:
            # Always logout and close the connection
            try:
                client.logout()
            except:
                pass

    async def fetch_emails(self) -> List[Mail]:
        """Fetch a limited number of recent emails asynchronously by running in a thread."""
        # Run the synchronous code in a thread pool
        return await asyncio.get_event_loop().run_in_executor(
            self._executor, self._fetch_emails_sync
        )
    
    def _fetch_emails_sync(self) -> List[Mail]:
        """Synchronous implementation of email fetching."""
        # Create a context with the desired protocol
        context = ssl.create_default_context()
        
        # Connect to the IMAP server
        client = imaplib.IMAP4_SSL(self.host, self.port, ssl_context=context)
        
        try:
            # Login
            client.login(self.auth.email, self.auth.password)
            
            # Select the inbox
            client.select("INBOX")
            
            # Search for all emails
            status, data = client.search(None, "ALL")
            if status != "OK":
                print(f"Error searching for emails: {status}")
                return []
            
            # Get the list of email IDs
            email_ids = data[0].split()
            
            # Take only the most recent emails (limited by max_emails)
            recent_ids = email_ids[-self.max_emails:] if email_ids else []
            
            emails = []
            for email_id in recent_ids:
                # Fetch the email
                status, data = client.fetch(email_id, "(RFC822)")
                if status != "OK":
                    print(f"Error fetching email {email_id}: {status}")
                    continue
                
                # The email content is in the second element of the first tuple in data
                raw_email = data[0][1]
                
                try:
                    # Parse the email
                    msg = email.message_from_bytes(raw_email, policy=default)
                    
                    # Create a Mail object
                    mail = Mail(
                        uid=email_id.decode(),
                        subject=msg["Subject"] or "",
                        from_=msg["From"] or "",
                        to=msg["To"] or "",
                        date=msg["Date"] or "",
                        body=self._get_email_body(msg)
                    )
                    emails.append(mail)
                except Exception as e:
                    print(f"Error parsing email {email_id}: {e}")
            
            return emails
        
        finally:
            # Always logout and close the connection
            try:
                client.close()
            except:
                pass
            client.logout()

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