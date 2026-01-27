"""
RAG Service - Simplified version using keyword search with auto-loading from database.
"""
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any, Optional

from core.config import settings


class RAGService:
    """
    RAG service with simple keyword search.
    Auto-loads documents from the database on first search.
    """
    
    _instance: Optional["RAGService"] = None
    _documents: List[Dict[str, Any]] = []
    _loaded: bool = False
    
    def __new__(cls):
        """Singleton pattern for shared resources."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        print("📚 RAG Service initialized (keyword search mode)")
    
    async def _ensure_loaded(self):
        """Ensure documents are loaded from database."""
        if RAGService._loaded:
            return
        
        db_path = Path(settings.NOTES_DB_PATH)
        if not db_path.exists():
            print(f"⚠️ Database not found: {db_path}")
            RAGService._loaded = True
            return
        
        try:
            async with aiosqlite.connect(str(db_path)) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT id, title, plainText, content FROM notes WHERE deletedAt IS NULL"
                )
                rows = await cursor.fetchall()
                
                RAGService._documents = []
                for row in rows:
                    RAGService._documents.append({
                        "id": row["id"],
                        "title": row["title"] or "无标题",
                        "content": row["plainText"] or row["content"] or "",
                    })
                
                RAGService._loaded = True
                print(f"✅ Loaded {len(RAGService._documents)} notes into search index")
        except Exception as e:
            print(f"❌ Error loading notes: {e}")
            RAGService._loaded = True
    
    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using improved keyword matching (Chinese-aware)."""
        await self._ensure_loaded()
        
        if len(RAGService._documents) == 0:
            return []
        
        query_lower = query.lower()
        results = []
        
        # For Chinese: extract meaningful characters (length >= 2) for matching
        # For English: use space splitting as before
        import re
        # Split by whitespace and Chinese punctuation, filter short tokens
        query_terms = [t for t in re.split(r'[\s，。！？、；：""''（）【】\n]+', query_lower) if len(t) >= 2]
        
        # If no terms extracted (short query), use the whole query as a single term
        if not query_terms:
            query_terms = [query_lower]
        
        print(f"🔎 Search terms: {query_terms}")
        
        for doc in RAGService._documents:
            content = doc.get("content", "").lower()
            title = doc.get("title", "").lower()
            combined = title + " " + content
            
            # Count matching terms (substring match)
            score = sum(1 for term in query_terms if term in combined)
            
            if score > 0:
                doc_copy = doc.copy()
                doc_copy["score"] = score / len(query_terms)
                results.append(doc_copy)
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    async def list_all_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List all notes (for 'what notes do I have' queries)."""
        await self._ensure_loaded()
        return RAGService._documents[:limit]
    
    async def add_document(self, doc_id: str, title: str, content: str) -> None:
        """Add a document to the search index."""
        for i, doc in enumerate(RAGService._documents):
            if doc.get("id") == doc_id:
                RAGService._documents[i] = {
                    "id": doc_id,
                    "title": title,
                    "content": content,
                }
                return
        
        RAGService._documents.append({
            "id": doc_id,
            "title": title,
            "content": content,
        })
    
    async def update_document(self, doc_id: str, title: str, content: str) -> None:
        """Update an existing document."""
        await self.add_document(doc_id, title, content)
    
    async def remove_document(self, doc_id: str) -> None:
        """Remove a document from the index."""
        RAGService._documents = [
            d for d in RAGService._documents if d.get("id") != doc_id
        ]
    
    async def reload(self) -> int:
        """Force reload from database."""
        RAGService._loaded = False
        RAGService._documents = []
        await self._ensure_loaded()
        return len(RAGService._documents)
