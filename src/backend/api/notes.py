"""
Notes API endpoints for direct note operations.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from services.note_service import NoteService

router = APIRouter()


class NoteCreate(BaseModel):
    """Note creation payload."""
    title: str = Field(..., description="Note title")
    content: str = Field(default="", description="Note content in HTML")
    category_id: Optional[str] = Field(None, description="Category ID")


class NoteUpdate(BaseModel):
    """Note update payload."""
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[str] = None


class NoteSearchRequest(BaseModel):
    """Semantic search request."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(default=5, description="Number of results")


@router.get("/")
async def list_notes():
    """List all notes."""
    try:
        service = NoteService()
        notes = await service.get_all_notes()
        return {"notes": notes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{note_id}")
async def get_note(note_id: str):
    """Get a specific note by ID."""
    try:
        service = NoteService()
        note = await service.get_note(note_id)
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_note(request: NoteCreate):
    """Create a new note."""
    try:
        service = NoteService()
        note = await service.create_note(
            title=request.title,
            content=request.content,
            category_id=request.category_id
        )
        return note
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{note_id}")
async def update_note(note_id: str, request: NoteUpdate):
    """Update an existing note."""
    try:
        service = NoteService()
        note = await service.update_note(
            note_id=note_id,
            title=request.title,
            content=request.content,
            category_id=request.category_id
        )
        if not note:
            raise HTTPException(status_code=404, detail="Note not found")
        return note
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
async def semantic_search(request: NoteSearchRequest):
    """
    Perform semantic search across all notes.
    Uses the vector store for similarity matching.
    """
    try:
        service = NoteService()
        results = await service.semantic_search(
            query=request.query,
            top_k=request.top_k
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reindex")
async def reindex_notes():
    """
    Rebuild the vector index from all notes.
    Called after significant data changes.
    """
    try:
        service = NoteService()
        count = await service.reindex_all()
        return {"status": "success", "indexed_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
