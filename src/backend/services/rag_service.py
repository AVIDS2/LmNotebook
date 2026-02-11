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


# Safe print for Windows GBK encoding
def safe_print(msg: str):
    """Print message safely on Windows by handling encoding errors."""
    try:
        print(msg)
    except UnicodeEncodeError:
        try:
            import sys
            sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
            sys.stdout.buffer.flush()
        except Exception:
            print(msg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))


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
        self._last_integrity_check_ms = 0
        self._integrity_check_interval_ms = 30000
        self._integrity_check_running = False

    def _get_embedding_fn(self):
        """Proxy-bypass Qwen Embedding Client."""
        if self.emb_fn is None:
            safe_print(f"[NET] Connecting to Cloud Embedding: {settings.EMBEDDING_MODEL}")
            
            class ProxyBypassEmbedder:
                def __init__(self, api_key, api_base, model_name):
                    self.api_key = api_key
                    self.api_base = api_base
                    self.model_name = model_name
                    # Bypass system proxy (Clash)
                    # Keep embedding calls bounded to avoid blocking chat/note workflows on network stalls.
                    self.client = httpx.Client(
                        trust_env=False,
                        timeout=httpx.Timeout(connect=8.0, read=20.0, write=20.0, pool=8.0),
                    )

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
                safe_print("[IO] Loading FAISS index from disk...")
                try:
                    self.index = faiss.read_index(str(self.index_file))
                    with open(self.meta_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.metadata = data.get("metadata", [])
                        self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
                    safe_print(f"[OK] FAISS Ready. {len(self.metadata)} items loaded.")
                except Exception as e:
                    safe_print(f"[WARN] FAISS Load failed: {e}. Starting fresh.")
                    self._create_empty_index()
            else:
                self._create_empty_index()

    def _create_empty_index(self):
        # Qwen text-embedding-v3 dimension is 1024
        dimension = 1024
        self.index = faiss.IndexFlatIP(dimension) # Inner Product is better for normalized embeddings
        self.metadata = []
        self.id_to_idx = {}
        safe_print("[OK] Created fresh FAISS index.")

    async def _ensure_loaded(self, allow_integrity_check: bool = True):
        if self.index is None:
            await self._init_resources()

        if allow_integrity_check:
            await self._maybe_incremental_sync_with_db()

        self._loaded_initial = True

    async def _maybe_incremental_sync_with_db(self):
        """
        Lightweight integrity sync:
        - Only reconcile missing/deleted IDs incrementally.
        - Avoid full re-index on normal request paths.
        """
        import time

        now_ms = int(time.time() * 1000)
        if now_ms - self._last_integrity_check_ms < self._integrity_check_interval_ms:
            return
        if self._is_syncing or self._integrity_check_running:
            return

        self._last_integrity_check_ms = now_ms
        self._integrity_check_running = True
        try:
            db_path = settings.NOTES_DB_PATH
            if not os.path.exists(db_path):
                return

            async with self._sync_lock:
                async with aiosqlite.connect(db_path) as db:
                    db.row_factory = aiosqlite.Row
                    cursor = await db.execute(
                        "SELECT id, title, plainText FROM notes WHERE isDeleted = 0"
                    )
                    rows = await cursor.fetchall()

                db_notes = {str(r["id"]): dict(r) for r in rows}
                db_ids = set(db_notes.keys())
                local_ids = set(self.id_to_idx.keys())

                missing_ids = db_ids - local_ids
                stale_ids = local_ids - db_ids

                if not missing_ids and not stale_ids:
                    return

                safe_print(
                    f"[SYNC] Incremental reconcile: +{len(missing_ids)} / -{len(stale_ids)}"
                )

                for stale_id in stale_ids:
                    await self._remove_document_internal(stale_id, persist=False)

                for doc_id in missing_ids:
                    note = db_notes[doc_id]
                    title = note.get("title") or "Untitled"
                    text = (note.get("plainText") or "").strip() or f"Title: {title}"
                    await self._upsert_document_internal(doc_id, title, text, persist=False)

                await self._save_to_disk()
                safe_print("[OK] Incremental reconcile complete.")
        except Exception as e:
            safe_print(f"[ERR] Incremental integrity sync failed: {e}")
        finally:
            self._integrity_check_running = False

    async def _vectorize(self, texts: Any) -> np.ndarray:
        """Convert text to normalized numpy embeddings with batch size limiting."""
        emb_fn = self._get_embedding_fn()
        
        # Ensure texts is a list
        if not isinstance(texts, list):
            texts = [texts]
        
        if not texts:
            return np.array([]).astype('float32')
        
        # Batch size limit for Aliyun Embedding API (max 10)
        BATCH_SIZE = 10
        all_embeddings = []
        
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i + BATCH_SIZE]
            batch_embs = await asyncio.to_thread(emb_fn.embed_documents, batch)
            all_embeddings.extend(batch_embs)
        
        arr = np.array(all_embeddings).astype('float32')
        # Normalize for Cosine Similarity via Inner Product
        faiss.normalize_L2(arr)
        return arr

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Semantic search using FAISS with keyword fallback."""
        await self._ensure_loaded()
        if not query.strip():
            return []
        
        # If index is empty, try keyword search as fallback
        if self.index.ntotal == 0:
            safe_print(f"[SEARCH] FAISS empty, trying keyword fallback for: \"{query}\"")
            return await self._keyword_search(query, top_k)
            
        safe_print(f"[SEARCH] FAISS Search: \"{query}\"")
        try:
            query_vec = await self._vectorize(query)
            # D = distances (scores), I = indices
            # Request more results to account for deleted notes
            D, I = self.index.search(query_vec, min(top_k * 2, self.index.ntotal))
            
            # Get valid (non-deleted) note IDs from database
            from core.config import settings
            valid_ids = set()
            try:
                async with aiosqlite.connect(settings.NOTES_DB_PATH) as db:
                    cursor = await db.execute("SELECT id FROM notes WHERE isDeleted = 0")
                    rows = await cursor.fetchall()
                    valid_ids = {str(row[0]) for row in rows}
            except Exception as e:
                safe_print(f"[WARN] Could not fetch valid IDs: {e}")
            
            output = []
            for i, idx in enumerate(I[0]):
                if idx == -1: continue
                meta = self.metadata[idx]
                # Filter out deleted notes
                if valid_ids and meta['id'] not in valid_ids:
                    safe_print(f"[SEARCH] Skipping deleted note: {meta['id']}")
                    continue
                output.append({
                    "id": meta['id'],
                    "content": meta['content'],
                    "title": meta['title'],
                    "score": round(float(D[0][i]), 4),
                })
                if len(output) >= top_k:
                    break
            
            results = sorted(output, key=lambda x: x["score"], reverse=True)
            
            # If semantic search found nothing, try keyword fallback
            if not results:
                safe_print(f"[SEARCH] Semantic search empty, trying keyword fallback")
                results = await self._keyword_search(query, top_k)
            
            return results
        except Exception as e:
            safe_print(f"[ERR] FAISS Search Error: {e}")
            # Fallback to keyword search on error
            return await self._keyword_search(query, top_k)
    
    async def _keyword_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Fallback keyword search directly on database."""
        try:
            db_path = settings.NOTES_DB_PATH
            async with aiosqlite.connect(db_path) as db:
                db.row_factory = aiosqlite.Row
                # Search in title and plainText using LIKE
                search_term = f"%{query}%"
                cursor = await db.execute("""
                    SELECT id, title, plainText as content 
                    FROM notes 
                    WHERE isDeleted = 0 
                      AND (title LIKE ? OR plainText LIKE ?)
                    ORDER BY updatedAt DESC
                    LIMIT ?
                """, (search_term, search_term, top_k))
                rows = await cursor.fetchall()
                results = []
                for r in rows:
                    results.append({
                        "id": str(r['id']),
                        "title": r['title'],
                        "content": r['content'][:500] if r['content'] else "",
                        "score": 0.5  # Keyword match score
                    })
                safe_print(f"[SEARCH] Keyword fallback found {len(results)} results")
                return results
        except Exception as e:
            safe_print(f"[ERR] Keyword search failed: {e}")
            return []

    async def list_all_notes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        List recent documents.
        Strategy: ALWAYS read from DB (single source of truth) to respect isDeleted flag.
        FAISS metadata is only for vector search, not for listing.
        """
        await self._ensure_loaded()
        
        # Always read from DB (respects isDeleted = 0 filter)
        try:
            db_path = settings.NOTES_DB_PATH
            async with aiosqlite.connect(db_path) as db:
                 db.row_factory = aiosqlite.Row
                 cursor = await db.execute("SELECT id, title FROM notes WHERE isDeleted = 0 ORDER BY updatedAt DESC LIMIT ?", (limit,))
                 rows = await cursor.fetchall()
                 return [{"id": str(r['id']), "title": r['title'], "content": ""} for r in rows]
        except Exception as e:
            safe_print(f"[ERR] SQL List Error: {e}")
            # Fallback to FAISS metadata only if DB fails
            items = self.metadata[-limit:]
            if items:
                return [{"id": m['id'], "title": m['title'], "content": ""} for m in reversed(items)]
            return []

    async def add_document(self, doc_id: str, title: str, content: str) -> None:
        """Add document with re-indexing support."""
        await self._ensure_loaded(allow_integrity_check=False)
        text = content if (content and content.strip()) else f"Title: {title}"
        
        try:
            async with self._sync_lock:
                await self._upsert_document_internal(doc_id, title, text, persist=True)
            safe_print(f"[OK] Added to FAISS: {title}")
        except Exception as e:
            import traceback
            safe_print(f"[ERR] FAISS Add Error: {e}")
            traceback.print_exc()

    async def _upsert_document_internal(self, doc_id: str, title: str, text: str, persist: bool = False) -> None:
        """Upsert a single document embedding without triggering expensive full rebuilds."""
        if doc_id in self.id_to_idx:
            self._remove_documents_internal([doc_id])

        embedding = await self._vectorize(text)
        if embedding.size == 0:
            return

        # Dynamic Dimension Check
        if self.index.d != embedding.shape[1]:
            safe_print(f"[WARN] Dimension Mismatch (Index: {self.index.d}, New: {embedding.shape[1]}). Rebuilding index...")
            if self.index.ntotal == 0:
                self.index = faiss.IndexFlatIP(embedding.shape[1])
            else:
                raise ValueError(
                    f"Embedding dimension mismatch: {self.index.d} vs {embedding.shape[1]}. "
                    "Please run reindex_all."
                )

        self.index.add(embedding)
        self.metadata.append({"id": doc_id, "title": title, "content": text})
        self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}

        if persist:
            await self._save_to_disk()

    async def remove_document(self, doc_id: str) -> None:
        """
        FAISS IndexFlat doesn't support easy deletion by ID without rebuilding.
        For small collections, we rebuild or just filter.
        """
        await self._ensure_loaded(allow_integrity_check=False)
        async with self._sync_lock:
            await self._remove_document_internal(doc_id, persist=True)

    async def _remove_document_internal(self, doc_id: str, persist: bool = False) -> None:
        """Remove a document without re-calling remote embedding API."""
        if doc_id not in self.id_to_idx:
            return

        safe_print(f"[DEL] Removing from FAISS: {doc_id}")
        try:
            self._remove_documents_internal([doc_id])
        except Exception as e:
            # Last-resort fallback: re-vectorize remaining docs if reconstruction is unavailable.
            safe_print(f"[WARN] Vector reconstruction failed, fallback to re-embed: {e}")
            self.metadata = [m for m in self.metadata if m['id'] != doc_id]
            texts = [m['content'] for m in self.metadata]
            new_embs = await self._vectorize(texts)
            dimension = new_embs.shape[1] if new_embs.shape[0] > 0 else 1024
            self.index = faiss.IndexFlatIP(dimension)
            if new_embs.size > 0:
                self.index.add(new_embs)
            self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}

        if persist:
            await self._save_to_disk()

    def _remove_documents_internal(self, doc_ids: List[str]) -> None:
        """Batch-remove documents from index using vector reconstruction (no embedding API calls)."""
        if not doc_ids:
            return

        remove_set = {doc_id for doc_id in doc_ids if doc_id in self.id_to_idx}
        if not remove_set:
            return

        total = self.index.ntotal
        if total == 0:
            self.metadata = [m for m in self.metadata if m['id'] not in remove_set]
            self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
            return

        remove_indices = {self.id_to_idx[doc_id] for doc_id in remove_set}
        vectors = self.index.reconstruct_n(0, total)
        keep_mask = np.ones(total, dtype=bool)
        for idx in remove_indices:
            if 0 <= idx < total:
                keep_mask[idx] = False
        kept_vectors = vectors[keep_mask]

        self.metadata = [m for m in self.metadata if m['id'] not in remove_set]
        self.index = faiss.IndexFlatIP(self.index.d)
        if kept_vectors.size > 0:
            self.index.add(kept_vectors.astype('float32'))
        self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}

    async def update_document(self, doc_id: str, title: str, content: str) -> None:
        await self._ensure_loaded(allow_integrity_check=False)
        text = content if (content and content.strip()) else f"Title: {title}"
        async with self._sync_lock:
            await self._upsert_document_internal(doc_id, title, text, persist=True)

    async def upsert_documents_batch(self, docs: List[Dict[str, str]]) -> int:
        """
        Batch upsert for frontend edit bursts.
        Expected item format: {"id": str, "title": str, "content": str}
        """
        if not docs:
            return 0

        await self._ensure_loaded(allow_integrity_check=False)
        async with self._sync_lock:
            # Keep last write per note in this batch.
            latest_by_id: Dict[str, Dict[str, str]] = {}
            for item in docs:
                doc_id = str(item.get("id", "")).strip()
                if not doc_id:
                    continue
                latest_by_id[doc_id] = item

            if not latest_by_id:
                return 0

            ordered_items = list(latest_by_id.values())
            remove_ids = [str(item["id"]) for item in ordered_items if str(item["id"]) in self.id_to_idx]
            if remove_ids:
                self._remove_documents_internal(remove_ids)

            texts = []
            titles = []
            ids = []
            for item in ordered_items:
                doc_id = str(item["id"])
                title = str(item.get("title") or "Untitled")
                content = str(item.get("content") or "")
                text = content.strip() if content.strip() else f"Title: {title}"
                ids.append(doc_id)
                titles.append(title)
                texts.append(text)

            embs = await self._vectorize(texts)
            if embs.size == 0:
                return 0

            if self.index.d != embs.shape[1]:
                if self.index.ntotal == 0:
                    self.index = faiss.IndexFlatIP(embs.shape[1])
                else:
                    raise ValueError(
                        f"Embedding dimension mismatch: {self.index.d} vs {embs.shape[1]}. "
                        "Please run reindex_all."
                    )

            self.index.add(embs)
            for doc_id, title, text in zip(ids, titles, texts):
                self.metadata.append({"id": doc_id, "title": title, "content": text})
            self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
            await self._save_to_disk()
            return len(ids)

    async def _save_to_disk(self):
        """Persist FAISS index and metadata with sync timestamp."""
        try:
            import time
            faiss.write_index(self.index, str(self.index_file))
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "metadata": self.metadata,
                    "last_sync_time": int(time.time() * 1000)  # Unix timestamp in ms (same as DB)
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            safe_print(f"[ERR] FAISS Save failed: {e}")

    async def reload(self) -> int:
        await self._init_resources()
        return len(self.metadata)

    async def reindex_from_db(self, notes: List[Dict[str, Any]]) -> int:
        """Full re-sync with FAISS."""
        if self._is_syncing: return 0
        await self._init_resources()

        async with self._sync_lock:
            self._is_syncing = True
            try:
                valid_notes = [n for n in notes if n.get('title') or n.get('plainText') or n.get('content')]
                if not valid_notes: return 0
                
                safe_print(f"[SYNC] Re-indexing {len(valid_notes)} notes into FAISS...")
                
                documents = []
                new_metadata = []
                for n in valid_notes:
                    text = n.get('plainText') or n.get('content') or ""
                    if not text.strip(): text = f"Title: {n.get('title', 'Untitled')}"
                    documents.append(text)
                    new_metadata.append({
                        "id": n['id'],
                        "title": n.get('title', 'Untitled'),
                        "content": text
                    })
                
                # Vectorize everything via API
                embeddings = await self._vectorize(documents)
                
                # Dynamic Dimension Detection: Don't guess, observe.
                if embeddings.shape[0] > 0:
                    dimension = embeddings.shape[1]
                else:
                    dimension = 1536 # Default fallback
                
                safe_print(f"[INFO] Detected Embedding Dimension: {dimension}")
                
                # Update memory state
                self.index = faiss.IndexFlatIP(dimension)
                
                # Ensure embeddings are correct shape/type for FAISS
                if embeddings.ndim != 2 or embeddings.shape[1] != dimension:
                    safe_print(f"[ERR] Embedding Shape Error: Expected (N, {dimension}), got {embeddings.shape}")
                    return 0
                
                self.index.add(embeddings)
                self.metadata = new_metadata
                self.id_to_idx = {m['id']: i for i, m in enumerate(self.metadata)}
                
                await self._save_to_disk()
                safe_print(f"[OK] FAISS Re-sync Complete. Count: {self.index.ntotal}")
                return len(self.metadata)
            except Exception as e:
                import traceback
                safe_print(f"[ERR] FAISS Re-sync Error: {e}")
                traceback.print_exc()
                return 0
            finally:
                self._is_syncing = False


