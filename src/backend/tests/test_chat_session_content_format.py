import sys
import unittest
from pathlib import Path

# Ensure src/backend is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from api import chat  # noqa: E402


class ChatSessionContentFormatTests(unittest.TestCase):
    def test_content_to_text_with_plain_string(self):
        self.assertEqual(chat._content_to_text("hello"), "hello")

    def test_content_to_text_with_multimodal_blocks(self):
        content = [
            {"type": "text", "text": "读取这张图"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,AAA"},
            },
            {"type": "text", "text": "并总结"},
        ]
        self.assertEqual(chat._content_to_text(content), "读取这张图 [Image] 并总结")

    def test_content_to_text_with_unknown_data(self):
        self.assertEqual(chat._content_to_text({"foo": "bar"}), "{'foo': 'bar'}")

    def test_content_to_text_strips_control_chain_and_private_use(self):
        content = "_WRITE_WRITE\uE123 已完成分类"
        self.assertEqual(chat._content_to_text(content), "已完成分类")


if __name__ == "__main__":
    unittest.main()
