from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from core.model_manager import model_manager

router = APIRouter()

class ProviderSchema(BaseModel):
    id: Optional[str] = None
    name: str
    baseUrl: str
    apiKey: str
    modelName: str
    isActive: bool = False

@router.get("/providers")
async def get_providers():
    return model_manager.get_providers()

@router.post("/providers")
async def add_provider(provider: ProviderSchema):
    data = provider.dict()
    if not data.get("id"):
        data["id"] = str(uuid.uuid4())
    return model_manager.add_provider(data)

@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, provider: ProviderSchema):
    updated = model_manager.update_provider(provider_id, provider.dict(exclude={"id"}))
    if not updated:
        raise HTTPException(status_code=404, detail="Provider not found")
    return updated

@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    model_manager.delete_provider(provider_id)
    return {"status": "success"}

@router.post("/providers/{provider_id}/active")
async def set_active_provider(provider_id: str):
    model_manager.set_active_provider(provider_id)
    return {"status": "ok"}

@router.post("/providers/reorder")
async def reorder_providers(data: dict):
    success = model_manager.reorder_providers(data.get("draggedId"), data.get("targetId"))
    if not success:
        return {"status": "error", "message": "Failed to reorder providers"}
    return {"status": "ok"}
