from ..types import Mail, ProcessedMail
import textwrap
from typing import List
import logging
import re
import trafilatura
from bs4 import BeautifulSoup

class MailProcessor:
    """Processes raw emails into chunks for embedding."""
    async def process_mail(self, mail: Mail) -> ProcessedMail:
        """Process a mail into chunks ready for embedding."""
        body = mail.body or ""
        
        # Clean and extract text from the email body
        cleaned_text = self._clean_email_body(body)
        
        # Split the cleaned text into chunks
        chunks = self._split_text(cleaned_text)
        
        # Add logging
        logging.info(f"Processing email: {mail.uid}, subject: {mail.subject}")
        logging.info(f"Original email length: {len(body)}, cleaned length: {len(cleaned_text)}")
        logging.info(f"Generated {len(chunks)} chunks for email {mail.uid}")
        
        # Return a single ProcessedMail with all chunks
        return ProcessedMail(
            mail_uid=mail.uid,
            chunks=chunks
        )

    def _clean_email_body(self, body: str) -> str:
        """Clean email body text, handling HTML content appropriately."""
        # Check if the body is HTML
        if self._is_html(body):
            logging.info("Detected HTML content, using trafilatura for extraction")
            # Use trafilatura to extract clean text from HTML
            extracted_text = trafilatura.extract(body)
            
            # If trafilatura fails, fallback to BeautifulSoup
            if not extracted_text:
                logging.info("Trafilatura extraction failed, falling back to BeautifulSoup")
                soup = BeautifulSoup(body, 'html.parser')
                extracted_text = soup.get_text(separator=' ', strip=True)
            
            # Clean up the extracted text
            cleaned_text = self._post_process_text(extracted_text or "")
            return cleaned_text
        else:
            # For plain text emails, just do basic cleaning
            return self._post_process_text(body)
    
    def _is_html(self, text: str) -> bool:
        """Determine if the text is likely HTML content."""
        # Simple check for HTML tags
        return bool(re.search(r'<\s*[a-zA-Z]+[^>]*>', text))
    
    def _post_process_text(self, text: str) -> str:
        """Post-process extracted text to make it more LLM-friendly."""
        if not text:
            return ""
            
        # Replace multiple newlines with a single one
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with a single one
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove common email signatures and footers
        text = re.sub(r'--+\s*\n.*', '', text, flags=re.DOTALL)
        
        # Remove common email reply patterns
        text = re.sub(r'On.*wrote:.*', '', text, flags=re.DOTALL)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '[URL]', text)
        
        return text.strip()

    def _split_text(self, text: str) -> list[str]:
        """Split text into chunks of appropriate size for embedding."""
        if not text:
            return []
            
        # Use a larger chunk size now that we have cleaner text
        chunks = textwrap.wrap(text, 1000)  # Split at 1000 chars
        return chunks