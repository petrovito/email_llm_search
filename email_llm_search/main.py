import uvicorn
from fastapi import FastAPI, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import asyncio
import logging
import os
import pathlib
from .mail_searcher_context import MailSearcherContext

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

context = None

@app.on_event("startup")
async def startup_event():
    """Initialize the context on startup."""
    global context
    logging.info("Starting up application")
    context = await MailSearcherContext().__aenter__()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logging.info("Shutting down application")
    await context.__aexit__(None, None, None)

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
    results = context.search(query.query, query.n_results)
    formatted_results = [
        {
            "id": results["ids"][0][i],
            "subject": results["metadatas"][0][i]["subject"],
            "from": results["metadatas"][0][i]["from"],
            "to": results["metadatas"][0][i]["to"],
            "date": results["metadatas"][0][i]["date"],
            "text": results["metadatas"][0][i]["text"],
            "distance": results["distances"][0][i]
        }
        for i in range(len(results["ids"][0]))
    ]
    return formatted_results

@app.get("/state")
async def get_state():
    """Return current state."""
    state = context.get_state()
    return {"last_sync_time": state.last_sync_time, "sync_status": state.sync_status}

@app.post("/sync")
async def sync(background_tasks: BackgroundTasks):
    """Trigger email sync in the background."""
    logging.info("Manual sync requested")
    background_tasks.add_task(context.sync_emails)
    return {"message": "Sync started in background"}

def run(host="0.0.0.0", port=8000):
    """Run the FastAPI application."""
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    run()