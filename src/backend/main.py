"""
Origin Notes Agent Backend
FastAPI server for AI agent functionality.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


# CRITICAL: Load .env before importing anything that uses config
if getattr(sys, 'frozen', False):
    # PyInstaller mode: .env is in temp folder
    base_path = sys._MEIPASS
    env_path = os.path.join(base_path, ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        safe_print(f"[ENV] Loaded from bundled: {env_path}")
    else:
        safe_print(f"[ENV] Warning: Bundled .env not found at {env_path}")
else:
    # Dev mode
    load_dotenv()

# FORCE IMPORT: Explicitly import critical dependencies to force PyInstaller to bundle them
# This bypasses any "hidden-import" detection issues
import markdown
import zhipuai
import langchain
import langchain_community
import langchain_openai
import uvicorn
import httpx

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.model_manager import model_manager
from api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Deeply simplified lifecycle."""
    safe_print(f">> Origin Notes Backend Ready on port {settings.PORT}")
    yield
    safe_print(">> Shutdown complete.")


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
    active = model_manager.get_active_provider()
    return {
        "status": "healthy",
        "version": "1.0.0",
        "provider": active["name"] if active else "Default",
        "llm_configured": bool(active.get("apiKey")) if active else False,
        "model": active.get("modelName") if active else settings.MODEL_NAME,
        "base_url": active.get("baseUrl") if active else settings.OPENAI_BASE_URL
    }


if __name__ == "__main__":
    import uvicorn
    import multiprocessing
    
    # Required for frozen executables using multiprocessing/uvicorn on Windows
    multiprocessing.freeze_support()
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=settings.PORT
    )
