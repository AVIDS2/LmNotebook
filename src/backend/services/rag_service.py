"""
RAG Service - Enterprise-grade Semantic Search using FAISS (Facebook AI Similarity Search).
Replacing ChromaDB for maximum stability on Windows.
"""
import os
import json
import numpy as np
import faiss
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
import httpx
import aiosqlite

from core.config import settings


class RAGService:
    """
    RAG service using FAISS for high-performance, stable semantic vector search.
    Decoupled architecture: API-based embeddings + Local FAISS indexing.
    """
    
    _instance: Optional["RAGService"] = None
    
    def __new__(cls):
        """Singleton pattern for shared resources."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Storage Paths
        self.save_path = Path(settings.VECTOR_STORE_PATH) / "faiss_v1_qwen"
        os.makedirs(self.save_path, exist_ok=True)
        self.index_file = self.save_path / "index.faiss"
        self.meta_file = self.save_path / "metadata.json"
        
        # In-memory resources
        self.index = None
        self.metadata = [] # List of {id, title, content}
        self.id_to_idx = {} # Map string ID to FAISS index
        
        self.emb_fn = None
        self._initialized = True
        self._loaded_initial = False
        self._sync_lock = asyncio.Lock()
        self._is_syncing = False

    def _get_embedding_fn(self):
        """Proxy-bypass Qwen Embedding Client."""
        if self.emb_fn is None:
            print(f"🌐 Connecting to Cloud Embedding: {settings.EMBEDDING_MODEL}")
            
            class ProxyBypassEmbedder:
                def __init__(self, api_key, api_base, model_name):
                    self.api_key = api_key
                    self.api_base = api_base
                    self.model_name = model_name
                    # Bypass system proxy (Clash)
                    self.client = httpx.Client(trust_env=False, timeout=60.0)

                def embed_documents(self, texts):
                    if not texts: return []
                    headers = {"Authorization": f"Bearer {self.api_key}"}
                    payload = {"model": self.model_name, "input": texts}
                    response = self.client.post(f"{self.api_base}/embeddings", json=payload, headers=headers)
                    if response.status_code != 200:
                        raise Exception(f"Embedding API Error: {response.text}")
                    return [d["embedding"] for d in response.json()["data"]]

            self.emb_fn = ProxyBypassEmbedder(
                api_key=settings.DASHSCOPE_API_KEY,
                api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
                model_name=settings.EMBEDDING_MODEL
            )
        return self.emb_fn

    async def _init_resources(self):
        """Lazy load FAISS index from disk or create new one."""
        async with self._sync_lock:
            if self.index is not None:
                return

            if self.index_file.exists() and self.meta_file.exists():
                print("📂 Loading FAISS index from disk...")
                try:
                    self.index = faiss.read_index(str(self.index_file))
                    with open(self.meta_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.metadata = data.get("metadata", [])
                        self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
                    print(f"✅ FAISS Ready. {len(self.metadata)} items loaded.")
                except Exception as e:
                    print(f"⚠️ FAISS Load failed: {e}. Starting fresh.")
                    self._create_empty_index()
            else:
                self._create_empty_index()

    def _create_empty_index(self):
        # Qwen text-embedding-v3 dimension is 1024
        dimension = 1024
        self.index = faiss.IndexFlatIP(dimension) # Inner Product is better for normalized embeddings
        self.metadata = []
        self.id_to_idx = {}
        print("✨ Created fresh FAISS index.")

    async def _ensure_loaded(self):
        if self.index is None:
            await self._init_resources()
            
        # Auto-Hydration: Check if we are empty but DB is not
        if self.index.ntotal == 0:
            try:
                # Direct check on DB to identify desync
                db_path = settings.NOTES_DB_PATH
                if os.path.exists(db_path):
                    async with aiosqlite.connect(db_path) as db:
                        db.row_factory = aiosqlite.Row
                        cursor = await db.execute("SELECT count(*) as count FROM notes WHERE isDeleted = 0")
                        row = await cursor.fetchone()
                        db_count = row['count'] if row else 0
                        
                    if db_count > 0:
                        print(f"🚨 Desync Detected: FAISS=0, DB={db_count}. Starting Auto-Hydration...")
                        # Fetch all notes manually to avoid circular dependency
                        async with aiosqlite.connect(db_path) as db:
                            db.row_factory = aiosqlite.Row
                            cursor = await db.execute("SELECT id, title, content, plainText FROM notes WHERE isDeleted = 0")
                            rows = await cursor.fetchall()
                            notes = [dict(r) for r in rows]
                        
                        # Trigger Vectorization
                        await self.reindex_from_db(notes)
            except Exception as e:
                print(f"❌ Auto-Hydration check failed: {e}")
                
        self._loaded_initial = True

    async def _vectorize(self, texts: Any) -> np.ndarray:
        """Convert text to normalized numpy embeddings."""
        emb_fn = self._get_embedding_fn()
        raw_embs = await asyncio.to_thread(emb_fn.embed_documents, texts if isinstance(texts, list) else [texts])
        arr = np.array(raw_embs).astype('float32')
        # Normalize for Cosine Similarity via Inner Product
        faiss.normalize_L2(arr)
        return arr

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search using FAISS."""
        await self._ensure_loaded()
        if not query.strip() or self.index.ntotal == 0:
            return []
            
        print(f"🔎 FAISS Search: \"{query}\"")
        try:
            query_vec = await self._vectorize(query)
            # D = distances (scores), I = indices
            D, I = self.index.search(query_vec, min(top_k, self.index.ntotal))
            
            output = []
            for i, idx in enumerate(I[0]):
                if idx == -1: continue
                meta = self.metadata[idx]
                output.append({
                    "id": meta['id'],
                    "content": meta['content'],
                    "title": meta['title'],
                    "score": round(float(D[0][i]), 4), # Cosine similarity since normalized
                })
            return sorted(output, key=lambda x: x["score"], reverse=True)
        except Exception as e:
            print(f"❌ FAISS Search Error: {e}")
            return []

    async def list_all_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent documents.
        Strategy: Try FAISS metadata first. If empty, fallback to DB to ensure data visibility.
        """
        await self._ensure_loaded()
        
        # 1. Try FAISS Metadata
        items = self.metadata[-limit:]
        if items:
            return [{"id": m['id'], "title": m['title'], "content": ""} for m in reversed(items)]
            
        # 2. Fallback to SQL DB directly if FAISS is empty (Safe Mode)
        print("⚠️ FAISS is empty, falling back to SQL for listing...")
        try:
            # We import here to avoid circular dependency issues if any
            from services.note_service import NoteService
            # We need to instantiate a temp service or use a raw query
            db_path = settings.NOTES_DB_PATH
            async with aiosqlite.connect(db_path) as db:
                 db.row_factory = aiosqlite.Row
                 cursor = await db.execute("SELECT id, title FROM notes WHERE isDeleted = 0 ORDER BY updatedAt DESC LIMIT ?", (limit,))
                 rows = await cursor.fetchall()
                 return [{"id": str(r['id']), "title": r['title'], "content": ""} for r in rows]
        except Exception as e:
            print(f"❌ SQL Fallback Error: {e}")
            return []

    async def add_document(self, doc_id: str, title: str, content: str) -> None:
        """Add document with re-indexing support."""
        await self._ensure_loaded()
        text = content if (content and content.strip()) else f"Title: {title}"
        
        try:
            # Check if exists and remove old
            if doc_id in self.id_to_idx:
                await self.remove_document(doc_id)
                
            embedding = await self._vectorize(text)
            
            # Dynamic Dimension Check
            if self.index.d != embedding.shape[1]:
                print(f"⚠️ Dimension Mismatch (Index: {self.index.d}, New: {embedding.shape[1]}). Rebuilding index...")
                # If dimension changed (e.g. model switch), we must rebuild index or error
                # For safety, let's error on add, but ideally reindex_all should be called
                # Here we will re-init index with new dimension for this item (clearing old)
                # WARNING: This clears old index if dimensions clash.
                # A safer approach is to raise error and ask user to reindex.
                # But for 'Agentic' self-healing, let's just accept the new one if index was empty-ish
                if self.index.ntotal == 0:
                     self.index = faiss.IndexFlatIP(embedding.shape[1])
                else:
                     raise ValueError(f"Embedding dimension mismatch: {self.index.d} vs {embedding.shape[1]}. Please run reindex_all.")

            self.index.add(embedding)
            self.metadata.append({"id": doc_id, "title": title, "content": text})
            self.id_to_idx[doc_id] = len(self.metadata) - 1
            
            # Save change
            await self._save_to_disk()
            print(f"✅ Added to FAISS: {title}")
        except Exception as e:
            import traceback
            print(f"❌ FAISS Add Error: {e}")
            traceback.print_exc()

    async def remove_document(self, doc_id: str) -> None:
        """
        FAISS IndexFlat doesn't support easy deletion by ID without rebuilding.
        For small collections, we rebuild or just filter.
        """
        if doc_id not in self.id_to_idx: return
        
        print(f"🗑️ Removing from FAISS: {doc_id}")
        self.metadata = [m for m in self.metadata if m['id'] != doc_id]
        # Rebuild index
        if not self.metadata:
            self._create_empty_index()
        else:
            texts = [m['content'] for m in self.metadata]
            new_embs = await self._vectorize(texts)
            
            dimension = new_embs.shape[1] if new_embs.shape[0] > 0 else 1024
            self.index = faiss.IndexFlatIP(dimension)
            self.index.add(new_embs)
            self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
        await self._save_to_disk()

    async def update_document(self, doc_id: str, title: str, content: str) -> None:
        await self.add_document(doc_id, title, content)

    async def _save_to_disk(self):
        """Persist FAISS index and metadata."""
        try:
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump({"metadata": self.metadata}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ FAISS Save failed: {e}")

    async def reload(self) -> int:
        await self._init_resources()
        return len(self.metadata)

    async def reindex_from_db(self, notes: List[Dict[str, Any]]) -> int:
        """Full re-sync with FAISS."""
        if self._is_syncing: return 0
        
        async with self._sync_lock:
            self._is_syncing = True
            try:
                await self._ensure_loaded()
                valid_notes = [n for n in notes if n.get('title') or n.get('plainText') or n.get('content')]
                if not valid_notes: return 0
                
                print(f"🔄 Re-indexing {len(valid_notes)} notes into FAISS...")
                
                documents = []
                new_metadata = []
                for n in valid_notes:
                    text = n.get('plainText') or n.get('content') or ""
                    if not text.strip(): text = f"Title: {n.get('title', '无标题')}"
                    documents.append(text)
                    new_metadata.append({
                        "id": n['id'],
                        "title": n.get('title', '无标题'),
                        "content": text
                    })
                
                # Vectorize everything via API
                embeddings = await self._vectorize(documents)
                
                # Dynamic Dimension Detection: Don't guess, observe.
                if embeddings.shape[0] > 0:
                    dimension = embeddings.shape[1]
                else:
                    dimension = 1536 # Default fallback
                
                print(f"📏 Detected Embedding Dimension: {dimension}")
                
                # Update memory state
                self.index = faiss.IndexFlatIP(dimension)
                
                # Ensure embeddings are correct shape/type for FAISS
                if embeddings.ndim != 2 or embeddings.shape[1] != dimension:
                    print(f"❌ Embedding Shape Error: Expected (N, {dimension}), got {embeddings.shape}")
                    return 0
                
                self.index.add(embeddings)
                self.metadata = new_metadata
                self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
                
                await self._save_to_disk()
                print(f"✅ FAISS Re-sync Complete. Count: {self.index.ntotal}")
                return len(self.metadata)
            except Exception as e:
                import traceback
                print(f"❌ FAISS Re-sync Error: {e}")
                traceback.print_exc()
                return 0
            finally:
                self._is_syncing = False
