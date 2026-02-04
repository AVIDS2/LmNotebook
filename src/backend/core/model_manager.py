import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from core.config import settings


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))

class ModelProvider:
    def __init__(self, id: str, name: str, baseUrl: str, apiKey: str, modelName: str, isActive: bool = False):
        self.id = id
        self.name = name
        self.baseUrl = baseUrl
        self.apiKey = apiKey
        self.modelName = modelName
        self.isActive = isActive

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "baseUrl": self.baseUrl,
            "apiKey": self.apiKey,
            "modelName": self.modelName,
            "isActive": self.isActive
        }

class ModelManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        # Store in user documents to persist across updates
        self.config_dir = Path(settings.VECTOR_STORE_PATH).parent
        self.config_file = self.config_dir / "models.json"
        self.providers: List[Dict[str, Any]] = []
        self._load_config()
        self._initialized = True

    def _load_config(self):
        if not self.config_file.exists():
            # Initial default provider from .env if available
            default_provider = {
                "id": "default",
                "name": "Default (from .env)",
                "baseUrl": settings.OPENAI_BASE_URL,
                "apiKey": settings.OPENAI_API_KEY,
                "modelName": settings.MODEL_NAME,
                "isActive": True
            }
            self.providers = [default_provider]
            self._save_config()
        else:
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.providers = json.load(f)
            except Exception as e:
                safe_print(f"[ERROR] Failed to load models.json: {e}")
                self.providers = []

    def _save_config(self):
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.providers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            safe_print(f"[ERROR] Failed to save models.json: {e}")

    def get_providers(self) -> List[Dict[str, Any]]:
        return self.providers

    def get_active_provider(self) -> Optional[Dict[str, Any]]:
        for p in self.providers:
            if p.get("isActive"):
                return p
        return self.providers[0] if self.providers else None

    def add_provider(self, provider: Dict[str, Any]):
        self.providers.append(provider)
        self._save_config()
        return provider

    def update_provider(self, provider_id: str, updates: Dict[str, Any]):
        for i, p in enumerate(self.providers):
            if p["id"] == provider_id:
                self.providers[i].update(updates)
                self._save_config()
                return self.providers[i]
        return None

    def delete_provider(self, provider_id: str):
        self.providers = [p for p in self.providers if p["id"] != provider_id]
        # Ensure at least one is active if we didn't delete everything
        if self.providers and not any(p.get("isActive") for p in self.providers):
            self.providers[0]["isActive"] = True
        self._save_config()

    def set_active_provider(self, provider_id: str):
        for p in self.providers:
            p["isActive"] = (p["id"] == provider_id)
        self._save_config()

    def reorder_providers(self, dragged_id: str, target_id: str):
        dragged_idx = -1
        target_idx = -1
        for i, p in enumerate(self.providers):
            if p["id"] == dragged_id:
                dragged_idx = i
            if p["id"] == target_id:
                target_idx = i
        
        if dragged_idx != -1 and target_idx != -1:
            provider = self.providers.pop(dragged_idx)
            self.providers.insert(target_idx, provider)
            self._save_config()
            return True
        return False

model_manager = ModelManager()
