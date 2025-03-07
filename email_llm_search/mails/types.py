from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from ..types import Mail

@dataclass
class MailingStatus:
    """Status of the mail synchronization."""
    total_emails: int
    synced_emails: int
    last_sync_time: Optional[datetime] = None
    is_syncing: bool = False
    error: Optional[str] = None 