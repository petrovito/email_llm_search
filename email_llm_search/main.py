import uvicorn
from fastapi import FastAPI
import asyncio
import logging
import os
import pathlib
import sys
from .mail_searcher import MailSearcher
from .controllers import RestController

# Configure logging to output to both file and console
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# # File handler
# file_handler = logging.FileHandler("app.log")
# file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
# logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(console_handler)

# Configure uvicorn logging
for uvicorn_logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
    uvicorn_logger = logging.getLogger(uvicorn_logger_name)
    uvicorn_logger.handlers = []  # Remove default handlers
    uvicorn_logger.propagate = True  # Propagate to root logger

# Get the directory of the current file
current_dir = pathlib.Path(__file__).parent.parent
static_dir = os.path.join(current_dir, "static")

app = FastAPI()
mail_searcher = None
rest_controller = None

@app.on_event("startup")
async def startup_event():
    """Initialize the mail searcher and controller on startup."""
    global mail_searcher, rest_controller
    logging.info("Starting up application")
    
    # Initialize mail searcher
    mail_searcher = MailSearcher()
    if not await mail_searcher.initialize():
        logging.error("Failed to initialize MailSearcher")
        exit(1)
    
    # Initialize REST controller
    rest_controller = RestController(app, mail_searcher, static_dir)
    
    # Start the email syncing process (non-blocking)
    await mail_searcher.start()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logging.info("Shutting down application")
    # No explicit cleanup needed

def run(host="0.0.0.0", port=8000):
    """Run the FastAPI application."""
    # Configure Uvicorn to use our logging settings
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_config=None,  # Disable Uvicorn's default logging config
        log_level="info"
    )

if __name__ == "__main__":
    run()