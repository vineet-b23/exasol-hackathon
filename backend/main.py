import os
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# -------------------------------------------------------------
# Path Resolution & Environment Configuration
# -------------------------------------------------------------
BACKEND_DIR = Path(__file__).resolve().parent
ROOT_DIR = BACKEND_DIR.parent

# Ensure backend directory is present in sys.path for absolute imports
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load .env from project root
load_dotenv(dotenv_path=ROOT_DIR / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Absolute import relative to backend directory
from api.routes import router as api_router

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("TRACE API is starting up...")
    logger.info("Connecting to internal engines and databases...")
    yield
    logger.info("TRACE API is shutting down...")

# Instantiate FastAPI App
app = FastAPI(
    title="TRACE API",
    description="Backend API for the internal investigation pipeline.",
    version="1.0.0",
    lifespan=lifespan
)

# -------------------------------------------------------------
# CORS Configuration
# -------------------------------------------------------------
origins = [
    "https://vineet-b23.github.io",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    max_age=3600,
)

# -------------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "TRACE API",
        "docs": "/docs"
    }

# Include the API router with prefix
app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    # Pass app object directly to avoid module resolution errors on direct run
    uvicorn.run(app, host="0.0.0.0", port=8000)