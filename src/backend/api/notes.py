"""
Notes API endpoints for direct note operations.
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from services.note_service import NoteService

router = APIRouter()


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode('gbk', errors='replace').decode('gbk'))


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


@router.delete("/{note_id}/vector")
async def remove_note_vector(note_id: str):
    """
    Remove a note from the vector index.
    Called when permanently deleting a note from trash.
    """
    try:
        service = NoteService()
        await service.rag_service.remove_document(note_id)
        return {"status": "success", "note_id": note_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BatchDeleteRequest(BaseModel):
    """Batch delete request for emptying trash."""
    note_ids: List[str] = Field(..., description="List of note IDs to remove from vector index")


@router.post("/vectors/batch-delete")
async def batch_remove_vectors(request: BatchDeleteRequest):
    """
    Remove multiple notes from the vector index.
    Called when emptying trash.
    """
    try:
        service = NoteService()
        removed = 0
        for note_id in request.note_ids:
            try:
                await service.rag_service.remove_document(note_id)
                removed += 1
            except Exception:
                pass  # Continue even if one fails
        return {"status": "success", "removed_count": removed}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class VectorSyncRequest(BaseModel):
    """Vector sync request for frontend note updates."""
    note_id: str = Field(..., description="Note ID")
    title: str = Field(..., description="Note title")
    content: str = Field(default="", description="Note plain text content")


@router.post("/vector/sync")
async def sync_note_vector(request: VectorSyncRequest):
    """
    Sync a note's vector index when updated from frontend.
    Called when user edits title or content directly in the editor.
    """
    try:
        service = NoteService()
        await service.rag_service.update_document(
            request.note_id,
            request.title,
            request.content
        )
        safe_print(f"[API] Vector synced for note: {request.title}")
        return {"status": "success", "note_id": request.note_id}
    except Exception as e:
        safe_print(f"[API] Vector sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
