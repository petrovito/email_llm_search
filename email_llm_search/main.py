import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import logging
import os
import pathlib
from .mail_searcher import MailSearcher
from .types import SearchResult

# Configure logging
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Get the directory of the current file
current_dir = pathlib.Path(__file__).parent.parent
static_dir = os.path.join(current_dir, "static")

app = FastAPI()
app.mount("/static", StaticFiles(directory=static_dir), name="static")

mail_searcher = None

@app.on_event("startup")
async def startup_event():
    """Initialize the mail searcher on startup."""
    global mail_searcher
    logging.info("Starting up application")
    mail_searcher = MailSearcher()
    if not await mail_searcher.initialize():
        logging.error("Failed to initialize MailSearcher")
        exit(1)
    
    # Start the email syncing process (non-blocking)
    await mail_searcher.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logging.info("Shutting down application")
    # No explicit cleanup needed

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the UI."""
    html_file = os.path.join(static_dir, "index.html")
    with open(html_file, "r") as f:
        return f.read()

class SearchQuery(BaseModel):
    """Schema for search query."""
    query: str
    n_results: int = 5

@app.post("/search")
async def search(query: SearchQuery):
    """Search emails and return top results."""
    logging.info(f"Searching for query: {query.query}")
    results = mail_searcher.search(query.query, query.n_results)
    
    # Convert SearchResult objects to dictionaries for JSON response
    formatted_results = [
        {
            "mail_uid": result.mail_uid,
            "chunk_index": result.chunk_index,
            "text": result.text,
            "score": result.score
        }
        for result in results
    ]
    
    return formatted_results

@app.get("/state")
async def get_state():
    """Return current state."""
    state = mail_searcher.get_state()
    return {"last_sync_time": state.last_sync_time, "sync_status": state.sync_status}

def run(host="0.0.0.0", port=8000):
    """Run the FastAPI application."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run()