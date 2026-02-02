"""
Configuration settings for the Agent Backend.
"""
import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings


def get_user_data_directory() -> Path:
    """Get the user-configured data directory from Electron config."""
    # Try to read from Electron's config file
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', '')
        config_path = Path(app_data) / 'origin-notes' / 'origin-notes-config.json'
    else:  # macOS/Linux
        config_path = Path.home() / '.config' / 'origin-notes' / 'origin-notes-config.json'
    
    # Default path
    default_path = Path.home() / "Documents" / "OriginNotes"
    
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                data_dir = config.get('dataDirectory')
                if data_dir:
                    return Path(data_dir)
    except Exception:
        pass
    
    return default_path


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
    
    # Paths - dynamically resolved from user config
    @property
    def data_directory(self) -> Path:
        return get_user_data_directory()
    
    @property
    def NOTES_DB_PATH(self) -> str:
        return str(self.data_directory / "notes.db")
    
    @property
    def VECTOR_STORE_PATH(self) -> str:
        return str(self.data_directory / "vectors")
    
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
