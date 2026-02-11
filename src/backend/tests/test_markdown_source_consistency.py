import sys
import tempfile
import unittest
from pathlib import Path

import aiosqlite

# Ensure src/backend is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.note_service import NoteService  # noqa: E402


class MarkdownSourceConsistencyTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "notes.db"
        self.service = NoteService()
        self.service.db_path = str(self.db_path)
        def _ignore_vector_task(coro, _label):
            try:
                coro.close()
            except Exception:
                pass
        self.service._run_vector_task = _ignore_vector_task

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE notes (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    plainText TEXT,
                    markdownSource TEXT,
                    categoryId TEXT,
                    isPinned INTEGER,
                    isDeleted INTEGER,
                    deletedAt INTEGER,
                    createdAt INTEGER,
                    updatedAt INTEGER
                )
                """
            )
            await db.execute(
                """
                INSERT INTO notes (
                    id, title, content, plainText, markdownSource, categoryId,
                    isPinned, isDeleted, deletedAt, createdAt, updatedAt
                ) VALUES (?, ?, ?, ?, ?, ?, 0, 0, NULL, ?, ?)
                """,
                (
                    "n1",
                    "Old",
                    "<h1>Old</h1><p>Legacy markdown content</p>",
                    "Old Legacy markdown content",
                    "# Old\n\nLegacy markdown content",
                    None,
                    1,
                    1,
                ),
            )
            await db.commit()

    async def asyncTearDown(self):
        self.tmpdir.cleanup()

    async def test_content_update_without_markdown_source_clears_stale_source(self):
        await self.service.update_note(note_id="n1", content="<p>Fresh html only</p>")
        updated = await self.service.get_note("n1")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["plainText"], "Fresh html only")
        self.assertIsNone(updated["markdownSource"])

    async def test_content_update_with_markdown_source_keeps_source(self):
        await self.service.update_note(
            note_id="n1",
            content="<h1>Title</h1><p>Body</p>",
            markdown_source="# Title\n\nBody",
        )
        updated = await self.service.get_note("n1")
        self.assertIsNotNone(updated)
        self.assertEqual(updated["markdownSource"], "# Title\n\nBody")

    async def test_stale_detection_rejects_diverged_markdown_source(self):
        stale = self.service._is_markdown_source_stale(
            markdown_source="# Shopping List\n\n- apple\n- banana\n- orange",
            plain_text="Release planning roadmap with sprint budget and risk tracking details.",
        )
        self.assertTrue(stale)

        aligned = self.service._is_markdown_source_stale(
            markdown_source="# Network Notes\n\n- NAT mapping\n- IPv6 routing",
            plain_text="Network Notes NAT mapping IPv6 routing",
        )
        self.assertFalse(aligned)


if __name__ == "__main__":
    unittest.main()
