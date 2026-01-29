"""
Origin Notes Agent Backend
FastAPI server for AI agent functionality.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Deeply simplified lifecycle."""
    print(f">> Origin Notes Backend Ready on port {settings.PORT}")
    yield
    print(">> Shutdown complete.")


app = FastAPI(
    title="Origin Notes Agent",
    description="AI-powered assistant for Origin Notes",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for Electron renderer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "llm_configured": bool(settings.OPENAI_API_KEY),
        "model": settings.MODEL_NAME,
        "base_url": settings.OPENAI_BASE_URL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=settings.PORT,
        reload=True
    )
