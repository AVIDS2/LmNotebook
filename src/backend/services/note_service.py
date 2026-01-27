"""
Note Service - Interface to the Origin Notes SQLite database.
Provides CRUD operations and bridges with the RAG service.
"""
import aiosqlite
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

from core.config import settings
from .rag_service import RAGService


class NoteService:
    """
    Service for note operations.
    
    Connects directly to the same SQLite database used by the Electron app.
    """
    
    def __init__(self):
        self.db_path = settings.NOTES_DB_PATH
        self.rag_service = RAGService()
    
    async def get_all_notes(self) -> List[Dict[str, Any]]:
        """Get all non-deleted notes."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT id, title, content, plainText, categoryId, isPinned, createdAt, updatedAt
                FROM notes
                WHERE isDeleted = 0
                ORDER BY updatedAt DESC
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific note by ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM notes WHERE id = ?",
                (note_id,)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def create_note(
        self,
        title: str,
        content: str = "",
        category_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new note."""
        note_id = f"{int(datetime.now().timestamp() * 1000)}-{uuid.uuid4().hex[:9]}"
        now = int(datetime.now().timestamp() * 1000)
        
        # Extract plain text from content
        plain_text = self._extract_plain_text(content)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO notes (
                    id, title, content, plainText, markdownSource,
                    categoryId, isPinned, isDeleted, deletedAt,
                    createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?)
            """, (
                note_id, title, content, plain_text, None,
                category_id, now, now
            ))
            await db.commit()
        
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "plainText": plain_text,
            "categoryId": category_id,
            "createdAt": now,
            "updatedAt": now,
        }
        
        # Add to vector store
        await self.rag_service.add_document(note_id, title, plain_text)
        
        return note
    
    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Update an existing note."""
        # Get current note
        current = await self.get_note(note_id)
        if not current:
            return None
        
        # Build update
        updates = {}
        if title is not None:
            updates["title"] = title
        if content is not None:
            updates["content"] = content
            updates["plainText"] = self._extract_plain_text(content)
        if category_id is not None:
            updates["categoryId"] = category_id
        
        if not updates:
            return current
        
        updates["updatedAt"] = int(datetime.now().timestamp() * 1000)
        
        # Build SQL
        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [note_id]
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                f"UPDATE notes SET {set_clause} WHERE id = ?",
                values
            )
            await db.commit()
        
        # Update vector store
        final_title = updates.get("title", current["title"])
        final_content = updates.get("plainText", current.get("plainText", ""))
        await self.rag_service.update_document(note_id, final_title, final_content)
        
        return await self.get_note(note_id)
    
    async def delete_note(self, note_id: str) -> bool:
        """Soft delete a note (move to trash)."""
        now = int(datetime.now().timestamp() * 1000)
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute(
                "UPDATE notes SET isDeleted = 1, deletedAt = ? WHERE id = ?",
                (now, note_id)
            )
            await db.commit()
            if result.rowcount > 0:
                # Remove from vector store
                await self.rag_service.remove_document(note_id)
                return True
        return False
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across notes."""
        return await self.rag_service.search(query, top_k)
    
    async def reindex_all(self) -> int:
        """Rebuild the vector index from all notes."""
        notes = await self.get_all_notes()
        return await self.rag_service.reindex_from_db(notes)
    
    def _extract_plain_text(self, html_content: str) -> str:
        """Extract plain text from HTML content."""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode common HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        text = text.replace('&quot;', '"')
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
