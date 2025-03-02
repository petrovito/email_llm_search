from dataclasses import dataclass
from typing import List, Optional

@dataclass
class ImapAuth:
    """IMAP authentication credentials."""
    email: str
    password: str

@dataclass
class State:
    """State of email syncing and embedding process."""
    last_sync_time: Optional[str] = None  # ISO format string
    sync_status: str = "idle"  # e.g., "idle", "syncing", "error"

@dataclass
class User:
    """User data combining auth and state, designed for single-user with extensibility."""
    auth: ImapAuth
    state: State

@dataclass
class Mail:
    """Raw email data fetched from IMAP."""
    uid: str
    subject: str
    from_: str  # 'from' is a Python keyword
    to: str
    date: str
    body: str

@dataclass
class ProcessedMail:
    """Processed email containing chunks ready for embedding."""
    mail_uid: str
    chunks: list[str]