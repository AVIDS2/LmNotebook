"""
Configuration settings for the Agent Backend.
"""
import os
import json
import platform
from pathlib import Path
from pydantic_settings import BaseSettings


def _config_path_candidates() -> list[Path]:
    """Return possible Electron config paths across platforms/legacy names."""
    env_override = (
        os.environ.get("LMNOTEBOOK_CONFIG_PATH", "").strip()
        or os.environ.get("ORIGIN_NOTES_CONFIG_PATH", "").strip()
    )
    if env_override:
        return [Path(env_override)]

    home = Path.home()
    candidates: list[Path] = []

    if os.name == 'nt':
        app_data = Path(os.environ.get('APPDATA', home / 'AppData' / 'Roaming'))
        candidates.extend([
            app_data / 'LmNotebook' / 'lmnotebook-config.json',
            app_data / 'lmnotebook' / 'lmnotebook-config.json',
            app_data / 'Origin Notes' / 'origin-notes-config.json',
            app_data / 'origin-notes' / 'origin-notes-config.json',
        ])
        return candidates

    # macOS
    if platform.system().lower() == 'darwin':
        candidates.extend([
            home / 'Library' / 'Application Support' / 'LmNotebook' / 'lmnotebook-config.json',
            home / 'Library' / 'Application Support' / 'lmnotebook' / 'lmnotebook-config.json',
            home / 'Library' / 'Application Support' / 'Origin Notes' / 'origin-notes-config.json',
            home / 'Library' / 'Application Support' / 'origin-notes' / 'origin-notes-config.json',
        ])
        return candidates

    # Linux / other unix
    xdg_config = Path(os.environ.get('XDG_CONFIG_HOME', home / '.config'))
    candidates.extend([
        xdg_config / 'LmNotebook' / 'lmnotebook-config.json',
        xdg_config / 'lmnotebook' / 'lmnotebook-config.json',
        xdg_config / 'Origin Notes' / 'origin-notes-config.json',
        xdg_config / 'origin-notes' / 'origin-notes-config.json',
    ])
    return candidates


def get_user_data_directory() -> Path:
    """Get the user-configured data directory from Electron config."""
    preferred_default = Path.home() / "Documents" / "LmNotebook"
    legacy_default = Path.home() / "Documents" / "OriginNotes"
    default_path = preferred_default if preferred_default.exists() or not legacy_default.exists() else legacy_default

    try:
        for config_path in _config_path_candidates():
            if not config_path.exists():
                continue
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
