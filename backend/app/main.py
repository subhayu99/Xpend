from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db

app = FastAPI(
    title="Finance Tracker API",
    description="Personal Finance Tracker with AI-powered categorization",
    version="1.0.0"
)

import logging

logger = logging.getLogger(__name__)

# CORS - Temporarily allowing all origins for testing
logger.info(f"Configuring CORS with origins: {settings.CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporarily allow all for testing
    allow_credentials=False,  # Must be False when using wildcard
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()

@app.get("/")
async def root():
    return {"message": "Finance Tracker API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

from app.api.v1.router import api_router
app.include_router(api_router)
