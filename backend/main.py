import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# -------------------------------------------------------------
# Load environment variables from .env in the project root
# -------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Absolute import relative to backend root directory
from api.routes import router as api_router

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logging message
    logger.info("TRACE API is starting up...")
    logger.info("Connecting to internal engines and databases...")
    yield
    # Shutdown logic
    logger.info("TRACE API is shutting down...")

# Instantiate FastAPI App
app = FastAPI(
    title="TRACE API",
    description="Backend API for the internal investigation pipeline.",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# Include the API router with prefix
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # Updated to main:app for direct execution
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)