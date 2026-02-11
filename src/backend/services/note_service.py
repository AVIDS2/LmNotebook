"""
Note Service - Interface to the Origin Notes SQLite database.
Provides CRUD operations and bridges with the RAG service.
"""
import aiosqlite
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import asyncio
import difflib
import re

from core.config import settings
from .rag_service import RAGService


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            import sys
            sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except Exception:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


class NoteService:
    """
    Service for note operations.
    
    Connects directly to the same SQLite database used by the Electron app.
    """
    
    def __init__(self):
        self.db_path = settings.NOTES_DB_PATH
        self.rag_service = RAGService()

    def _run_vector_task(self, coro, label: str) -> None:
        """Run vector sync in background so note CRUD is never blocked by embedding API latency."""
        async def _wrapped():
            try:
                await coro
            except Exception as e:
                safe_print(f"[WARN] Vector task failed ({label}): {e}")
        asyncio.create_task(_wrapped())
    
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
            if not row:
                return None
            note = dict(row)
            # If markdownSource diverges heavily from current plainText, treat it as stale.
            # This prevents the agent from reading obsolete content after rich-text edits.
            if self._is_markdown_source_stale(note.get("markdownSource"), note.get("plainText")):
                note["markdownSource"] = None
            return note
    
    async def create_note(
        self,
        title: str,
        content: str = "",
        category_id: Optional[str] = None,
        markdown_source: Optional[str] = None
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
                note_id, title, content, plain_text, markdown_source,
                category_id, now, now
            ))
            await db.commit()
        
        note = {
            "id": note_id,
            "title": title,
            "content": content,
            "plainText": plain_text,
            "markdownSource": markdown_source,
            "categoryId": category_id,
            "createdAt": now,
            "updatedAt": now,
        }
        
        # Add to vector store in background (non-blocking for UX)
        self._run_vector_task(
            self.rag_service.add_document(note_id, title, plain_text),
            f"create:{note_id}"
        )
        
        return note
    
    async def update_note(
        self,
        note_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        category_id: Optional[str] = None,
        markdown_source: Optional[str] = None
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
            # IMPORTANT:
            # If caller updates rendered HTML content but does not provide a synchronized
            # markdown_source, clear stale markdownSource by default to prevent
            # "editor display != agent read source" divergence.
            if markdown_source is None:
                updates["markdownSource"] = None
        if category_id is not None:
            updates["categoryId"] = category_id
        if markdown_source is not None:
            updates["markdownSource"] = markdown_source
        
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
        
        # Update vector store in background (non-blocking for UX)
        final_title = updates.get("title", current["title"])
        final_content = updates.get("plainText", current.get("plainText", ""))
        self._run_vector_task(
            self.rag_service.update_document(note_id, final_title, final_content),
            f"update:{note_id}"
        )
        
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
                # Remove from vector store in background (non-blocking for UX)
                self._run_vector_task(
                    self.rag_service.remove_document(note_id),
                    f"delete:{note_id}"
                )
                return True
        return False
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Perform semantic search across notes."""
        return await self.rag_service.search(query, top_k)
    
    async def get_all_categories(self) -> List[Dict[str, Any]]:
        """Get all categories."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT id, name, color, "order"
                FROM categories
                ORDER BY "order" ASC
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def set_note_category(self, note_id: str, category_id: Optional[str]) -> bool:
        """Set or clear a note's category."""
        async with aiosqlite.connect(self.db_path) as db:
            result = await db.execute(
                "UPDATE notes SET categoryId = ?, updatedAt = ? WHERE id = ? AND isDeleted = 0",
                (category_id, int(datetime.now().timestamp() * 1000), note_id)
            )
            await db.commit()
            return result.rowcount > 0
    
    async def reindex_all(self) -> int:
        """Rebuild the vector index from all notes."""
        notes = await self.get_all_notes()
        return await self.rag_service.reindex_from_db(notes)
    
    def _extract_plain_text(self, html_content: str) -> str:
        """Extract plain text from HTML content."""
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

    def _normalize_for_similarity(self, text: Optional[str]) -> str:
        if not text:
            return ""
        normalized = re.sub(r'<[^>]+>', ' ', text)
        normalized = re.sub(r'[`*_>#\-\[\]\(\)!|:~]+', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip().lower()
        return normalized

    def _is_markdown_source_stale(self, markdown_source: Optional[str], plain_text: Optional[str]) -> bool:
        if not markdown_source or not plain_text:
            return False

        md_norm = self._normalize_for_similarity(markdown_source)
        plain_norm = self._normalize_for_similarity(plain_text)
        if len(md_norm) < 24 or len(plain_norm) < 24:
            return False
        if md_norm == plain_norm:
            return False

        md_probe = md_norm[:120]
        plain_probe = plain_norm[:120]
        if (md_probe and md_probe in plain_norm) or (plain_probe and plain_probe in md_norm):
            return False

        ratio = difflib.SequenceMatcher(None, md_norm[:6000], plain_norm[:6000]).ratio()
        # Previous threshold (0.20) was too permissive and let clearly stale markdownSource pass.
        return ratio < 0.62

