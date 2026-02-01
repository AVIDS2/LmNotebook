"""
Configuration settings for the Agent Backend.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Universal LLM Settings (OpenAI Protocol)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-3-flash")
    
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")
    
    # Server
    PORT: int = 8765
    
    # Paths
    NOTES_DB_PATH: str = str(
        Path.home() / "Documents" / "OriginNotes" / "notes.db"
    )
    
    # Vector store
    VECTOR_STORE_PATH: str = str(
        Path.home() / "Documents" / "OriginNotes" / "vectors"
    )
    
    # Embeddings
    EMBEDDING_MODE: str = os.getenv("EMBEDDING_MODE", "api")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "embedding-2")
    
    # RAG settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    class Config:
        # Smart .env resolution for PyInstaller
        import sys
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            base_path = sys._MEIPASS
            env_file = os.path.join(base_path, ".env")
        else:
            # Running from source
            env_file = ".env"
            
        extra = "ignore"


settings = Settings()
