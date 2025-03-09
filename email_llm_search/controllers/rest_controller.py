from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import logging
import os
import pathlib
from typing import List

from ..mail_searcher import MailSearcher
from .rest_types import SearchQuery, SearchResultResponse, StateResponse

class RestController:
    """Controller for REST endpoints."""
    
    def __init__(self, app: FastAPI, mail_searcher: MailSearcher, static_dir: str):
        """Initialize the REST controller.
        
        Args:
            app: The FastAPI application
            mail_searcher: The MailSearcher instance
            static_dir: Directory containing static files
        """
        self.app = app
        self.mail_searcher = mail_searcher
        self.static_dir = static_dir
        
        # Register routes
        self._register_routes()
    
    def _register_routes(self):
        """Register all routes with the FastAPI application."""
        # Mount static files
        self.app.mount("/static", StaticFiles(directory=self.static_dir), name="static")
        
        # Register route handlers
        self.app.get("/")(self.read_root)
        self.app.post("/search")(self.search)
        self.app.get("/state")(self.get_state)
    
    async def read_root(self) -> HTMLResponse:
        """Serve the UI."""
        html_file = os.path.join(self.static_dir, "index.html")
        try:
            with open(html_file, "r") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            logging.error(f"HTML file not found: {html_file}")
            raise HTTPException(status_code=500, detail="UI file not found")
    
    async def search(self, query: SearchQuery) -> List[SearchResultResponse]:
        """Search emails and return top results."""
        logging.info(f"Searching for query: {query.query}")
        
        try:
            results = self.mail_searcher.search(query.query, query.n_results)
            
            # Convert SearchResult objects to SearchResultResponse objects
            return [
                SearchResultResponse(
                    mail_uid=result.mail_uid,
                    chunk_index=result.chunk_index,
                    text=result.text,
                    score=result.score
                )
                for result in results
            ]
        except Exception as e:
            logging.error(f"Error searching emails: {e}")
            raise HTTPException(status_code=500, detail=f"Error searching emails: {str(e)}")
    
    async def get_state(self) -> StateResponse:
        """Return current state."""
        try:
            state = self.mail_searcher.get_state()
            return StateResponse(
                last_sync_time=state.last_sync_time,
                sync_status=state.sync_status
            )
        except Exception as e:
            logging.error(f"Error getting state: {e}")
            raise HTTPException(status_code=500, detail=f"Error getting state: {str(e)}") 