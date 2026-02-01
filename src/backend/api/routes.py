"""
API routes initialization.
"""
from fastapi import APIRouter

from .chat import router as chat_router
from .notes import router as notes_router
from .models import router as models_router

router = APIRouter()

router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(notes_router, prefix="/notes", tags=["Notes"])
router.include_router(models_router, prefix="/models", tags=["Models"])
