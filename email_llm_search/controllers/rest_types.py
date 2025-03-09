from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Input types
class SearchQuery(BaseModel):
    """Schema for search query."""
    query: str
    n_results: int = 5

# Output types
class SearchResultResponse(BaseModel):
    """Schema for search result response."""
    mail_uid: str
    chunk_index: int
    text: str
    score: float

class StateResponse(BaseModel):
    """Schema for state response."""
    last_sync_time: Optional[str] = None
    sync_status: str = "idle" 