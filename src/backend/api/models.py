from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uuid
from core.model_manager import model_manager
from agent.supervisor import invalidate_agent_runtime_cache

router = APIRouter()

class ProviderSchema(BaseModel):
    id: Optional[str] = None
    name: str
    baseUrl: str
    apiKey: str
    modelName: str
    models: Optional[List[str]] = None
    activeModel: Optional[str] = None
    isActive: bool = False


class ActiveModelSchema(BaseModel):
    modelName: str

@router.get("/providers")
async def get_providers():
    return model_manager.get_providers()

@router.post("/providers")
async def add_provider(provider: ProviderSchema):
    data = provider.dict()
    if not data.get("id"):
        data["id"] = str(uuid.uuid4())
    created = model_manager.add_provider(data)
    await invalidate_agent_runtime_cache()
    return created

@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, provider: ProviderSchema):
    updated = model_manager.update_provider(provider_id, provider.dict(exclude={"id"}))
    if not updated:
        raise HTTPException(status_code=404, detail="Provider not found")
    await invalidate_agent_runtime_cache()
    return updated

@router.delete("/providers/{provider_id}")
async def delete_provider(provider_id: str):
    model_manager.delete_provider(provider_id)
    await invalidate_agent_runtime_cache()
    return {"status": "success"}

@router.post("/providers/{provider_id}/active")
async def set_active_provider(provider_id: str):
    model_manager.set_active_provider(provider_id)
    await invalidate_agent_runtime_cache()
    return {"status": "ok"}


@router.post("/providers/{provider_id}/models/active")
async def set_active_model(provider_id: str, payload: ActiveModelSchema):
    success = model_manager.set_provider_active_model(provider_id, payload.modelName)
    if not success:
        raise HTTPException(status_code=400, detail="Model not found in provider")
    await invalidate_agent_runtime_cache()
    return {"status": "ok"}

@router.post("/providers/reorder")
async def reorder_providers(data: dict):
    success = model_manager.reorder_providers(data.get("draggedId"), data.get("targetId"))
    if not success:
        return {"status": "error", "message": "Failed to reorder providers"}
    await invalidate_agent_runtime_cache()
    return {"status": "ok"}
