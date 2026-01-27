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
    
    # Specific API Keys (for backward compatibility or specific SDKs)
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GLM_API_KEY: str = os.getenv("GLM_API_KEY", "")
    
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
    EMBEDDING_MODEL: str = "BAAI/bge-small-zh-v1.5"
    
    # RAG settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
