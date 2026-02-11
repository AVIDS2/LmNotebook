import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

# Ensure src/backend is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.rag_service import RAGService  # noqa: E402


def _fake_embedding_for_text(text: str) -> np.ndarray:
    vec = np.zeros((1024,), dtype="float32")
    # deterministic but different enough for tests
    vec[0] = float((len(text) % 11) + 1)
    return vec


class RagIncrementalIndexingTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        RAGService._instance = None
        self.tmpdir = tempfile.TemporaryDirectory()
        self.service = RAGService()
        base = Path(self.tmpdir.name)
        self.service.save_path = base
        self.service.index_file = base / "index.faiss"
        self.service.meta_file = base / "metadata.json"
        self.service._create_empty_index()

        self.vectorize_call_count = 0

        async def fake_vectorize(texts):
            self.vectorize_call_count += 1
            if not isinstance(texts, list):
                texts = [texts]
            arr = np.vstack([_fake_embedding_for_text(str(t)) for t in texts]).astype("float32")
            # Keep same behavior as production code.
            import faiss
            faiss.normalize_L2(arr)
            return arr

        self.service._vectorize = fake_vectorize

    async def asyncTearDown(self):
        self.tmpdir.cleanup()
        RAGService._instance = None

    async def test_remove_document_does_not_reembed_remaining_docs(self):
        await self.service.add_document("n1", "Note 1", "alpha")
        await self.service.add_document("n2", "Note 2", "beta")

        # Reset counter and remove one doc.
        self.vectorize_call_count = 0
        await self.service.remove_document("n1")

        self.assertEqual(self.vectorize_call_count, 0, "remove_document should not call embedding API")
        self.assertEqual(self.service.index.ntotal, 1)
        self.assertNotIn("n1", self.service.id_to_idx)
        self.assertIn("n2", self.service.id_to_idx)

    async def test_update_document_only_embeds_updated_doc(self):
        await self.service.add_document("n1", "Note 1", "alpha")
        await self.service.add_document("n2", "Note 2", "beta")

        self.vectorize_call_count = 0
        await self.service.update_document("n1", "Note 1", "alpha updated")

        # One embedding call for the updated doc only.
        self.assertEqual(self.vectorize_call_count, 1)
        self.assertEqual(self.service.index.ntotal, 2)
        self.assertEqual(len(self.service.metadata), 2)

    async def test_batch_upsert_embeds_batch_once(self):
        await self.service.add_document("n1", "Note 1", "alpha")
        await self.service.add_document("n2", "Note 2", "beta")

        self.vectorize_call_count = 0
        count = await self.service.upsert_documents_batch(
            [
                {"id": "n1", "title": "Note 1", "content": "alpha updated"},
                {"id": "n2", "title": "Note 2", "content": "beta updated"},
                {"id": "n3", "title": "Note 3", "content": "gamma"},
            ]
        )

        self.assertEqual(count, 3)
        self.assertEqual(self.vectorize_call_count, 1, "batch upsert should vectorize in one call")
        self.assertEqual(self.service.index.ntotal, 3)
        self.assertIn("n1", self.service.id_to_idx)
        self.assertIn("n2", self.service.id_to_idx)
        self.assertIn("n3", self.service.id_to_idx)


if __name__ == "__main__":
    unittest.main()
