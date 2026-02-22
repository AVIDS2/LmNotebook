import sys
import unittest
from pathlib import Path
from unittest.mock import patch, AsyncMock

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Ensure src/backend is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent.graph import NoteAgentGraph  # noqa: E402
from agent.supervisor import AgentSupervisor  # noqa: E402
import agent.graph as graph_module  # noqa: E402


class _FakeModel:
    def __init__(self, response: AIMessage):
        self._response = response

    def invoke(self, _messages):
        return self._response


class GraphToolCallIntegrityTests(unittest.TestCase):
    def _build_graph(self, response: AIMessage) -> NoteAgentGraph:
        graph = NoteAgentGraph.__new__(NoteAgentGraph)
        fake_model = _FakeModel(response)
        graph.model_with_tools = fake_model
        graph.model_with_read_tools = fake_model
        graph._classify_write_authorization = lambda _history: True
        return graph

    def test_agent_node_keeps_only_first_tool_call(self):
        response = AIMessage(
            content="",
            tool_calls=[
                {"id": "call_1", "name": "list_categories", "args": {}},
                {"id": "call_2", "name": "create_note", "args": {"title": "x", "content": "y"}},
            ],
        )
        graph = self._build_graph(response)

        result = graph._agent_node(
            {
                "messages": [HumanMessage(content="帮我写一篇笔记并分类到工作")],
                "agent_mode": "agent",
                "intent": "TASK",
                "tool_call_count": 0,
            }
        )

        ai_msg = result["messages"][0]
        self.assertEqual(len(ai_msg.tool_calls), 1)
        self.assertEqual(ai_msg.tool_calls[0]["id"], "call_1")
        self.assertEqual(ai_msg.tool_calls[0]["name"], "list_categories")

    def test_agent_node_assigns_tool_call_id_when_missing(self):
        response = AIMessage(
            content="",
            tool_calls=[
                {"id": "", "name": "list_categories", "args": {}},
                {"id": "", "name": "create_note", "args": {"title": "x", "content": "y"}},
            ],
        )
        graph = self._build_graph(response)

        result = graph._agent_node(
            {
                "messages": [HumanMessage(content="帮我写一篇笔记并分类到工作")],
                "agent_mode": "agent",
                "intent": "TASK",
                "tool_call_count": 0,
            }
        )

        ai_msg = result["messages"][0]
        self.assertEqual(len(ai_msg.tool_calls), 1)
        self.assertTrue(str(ai_msg.tool_calls[0]["id"]).startswith("call_"))

    def test_extract_requested_category_hint_from_chinese_prompt(self):
        graph = self._build_graph(AIMessage(content="ok"))
        hint = graph._extract_requested_category_hint("帮我写一篇笔记，主题是宇树科技的发展史，归类到工作")
        self.assertEqual(hint, "工作")

    def test_agent_node_recovers_tool_call_from_invalid_tool_calls(self):
        response = AIMessage(
            content="I will create it.",
            tool_calls=[],
            invalid_tool_calls=[
                {
                    "type": "invalid_tool_call",
                    "id": "call_invalid_1",
                    "name": "create_note",
                    "args": "{\"title\":\"宇树科技的发展史\",\"content\":\"内容\"}",
                    "error": None,
                }
            ],
        )
        graph = self._build_graph(response)

        result = graph._agent_node(
            {
                "messages": [HumanMessage(content="帮我写一篇笔记，主题是宇树科技的发展史")],
                "agent_mode": "agent",
                "intent": "TASK",
                "tool_call_count": 0,
            }
        )

        ai_msg = result["messages"][0]
        self.assertEqual(len(ai_msg.tool_calls), 1)
        self.assertEqual(ai_msg.tool_calls[0]["name"], "create_note")
        self.assertEqual(ai_msg.tool_calls[0]["id"], "call_invalid_1")
        self.assertIsInstance(ai_msg.tool_calls[0]["args"], dict)

    def test_sanitize_history_strips_invalid_tool_calls_before_provider(self):
        graph = self._build_graph(AIMessage(content="ok"))
        history = [
            HumanMessage(content="写一篇笔记"),
            AIMessage(
                content="I'll do it",
                tool_calls=[],
                invalid_tool_calls=[
                    {
                        "type": "invalid_tool_call",
                        "id": "call_bad",
                        "name": "create_note",
                        "args": "{\"title\":\"x\"}",
                        "error": None,
                    }
                ],
            ),
            ToolMessage(content="done", tool_call_id="call_bad"),
        ]

        sanitized = graph._sanitize_history_for_provider(history)
        self.assertEqual(len(sanitized), 3)
        ai_msg = sanitized[1]
        self.assertEqual(getattr(ai_msg, "type", ""), "ai")
        self.assertEqual(getattr(ai_msg, "tool_calls", []), [])
        self.assertEqual(getattr(ai_msg, "invalid_tool_calls", []), [])

    def test_strip_pre_tool_content_keeps_tool_calls_but_clears_chatter(self):
        graph = self._build_graph(AIMessage(content="ok"))
        response = AIMessage(
            content="Sure thing! I will create the note now.",
            tool_calls=[{"id": "call_1", "name": "create_note", "args": {"title": "x", "content": "y"}}],
        )

        cleaned = graph._strip_pre_tool_content(response)
        self.assertEqual(cleaned.content, "")
        self.assertEqual(len(cleaned.tool_calls), 1)
        self.assertEqual(cleaned.tool_calls[0]["name"], "create_note")

    def test_normalize_note_id_prefers_context_note_for_read_tool(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }

        normalized = graph._normalize_note_id_args({}, state, tool_name="read_note_content")
        self.assertEqual(normalized.get("note_id"), "context-note-id")

    def test_normalize_note_id_prefers_active_note_for_write_tool(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }

        normalized = graph._normalize_note_id_args({}, state, tool_name="update_note")
        self.assertEqual(normalized.get("note_id"), "active-note-id")

    def test_read_note_content_overrides_to_context_note_by_default(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }
        history = [HumanMessage(content="这个笔记的内容是什么？")]

        normalized = graph._normalize_note_id_args(
            {"note_id": "active-note-id"},
            state,
            tool_name="read_note_content",
            history=history,
        )
        self.assertEqual(normalized.get("note_id"), "context-note-id")

    def test_read_note_content_keeps_active_when_user_explicitly_says_current_note(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }
        history = [HumanMessage(content="读取当前笔记的内容")]

        normalized = graph._normalize_note_id_args(
            {"note_id": "active-note-id"},
            state,
            tool_name="read_note_content",
            history=history,
        )
        self.assertEqual(normalized.get("note_id"), "active-note-id")

    def test_referenced_note_content_query_detected_for_attachment_language(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }
        self.assertTrue(
            graph._is_referenced_note_content_query("我说的是附件的这个笔记，不是当前笔记", state)
        )

    def test_referenced_note_content_query_not_detected_for_explicit_current_note(self):
        graph = self._build_graph(AIMessage(content="ok"))
        state = {
            "active_note_id": "active-note-id",
            "context_note_id": "context-note-id",
        }
        self.assertFalse(
            graph._is_referenced_note_content_query("读取当前笔记的内容", state)
        )


class SupervisorPendingInterruptTests(unittest.IsolatedAsyncioTestCase):
    async def test_has_pending_interrupt_detects_interrupt_write_row(self):
        supervisor = AgentSupervisor.__new__(AgentSupervisor)

        class _FakeCursor:
            def __init__(self, fetchone_result=None, fetchall_result=None):
                self._fetchone_result = fetchone_result
                self._fetchall_result = fetchall_result or []

            async def fetchone(self):
                return self._fetchone_result

            async def fetchall(self):
                return self._fetchall_result

        class _FakeConnection:
            def __init__(self, pending_count):
                self._pending_count = pending_count

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def execute(self, sql, params=()):
                normalized = " ".join(str(sql).split()).lower()
                if "from checkpoints" in normalized and "select checkpoint_id" in normalized:
                    return _FakeCursor(fetchone_result=("cp_latest",))
                if normalized.startswith("pragma table_info(writes)"):
                    return _FakeCursor(
                        fetchall_result=[
                            (0, "thread_id", "TEXT", 1, None, 1),
                            (1, "checkpoint_ns", "TEXT", 1, "''", 2),
                            (2, "checkpoint_id", "TEXT", 1, None, 3),
                            (3, "task_id", "TEXT", 1, None, 4),
                            (4, "idx", "INTEGER", 1, None, 5),
                            (5, "channel", "TEXT", 1, None, 0),
                            (6, "type", "TEXT", 0, None, 0),
                            (7, "value", "BLOB", 0, None, 0),
                        ]
                    )
                if "from writes" in normalized and "channel = '__interrupt__'" in normalized:
                    return _FakeCursor(fetchone_result=(self._pending_count,))
                raise AssertionError(f"Unexpected SQL in test: {sql} / params={params}")

        original_path = graph_module.CHECKPOINT_DB_PATH
        graph_module.CHECKPOINT_DB_PATH = "mock-checkpoints.db"
        try:
            with patch("aiosqlite.connect", return_value=_FakeConnection(1)):
                self.assertTrue(await supervisor._has_pending_interrupt("session-1"))
            with patch("aiosqlite.connect", return_value=_FakeConnection(0)):
                self.assertFalse(await supervisor._has_pending_interrupt("session-2"))
        finally:
            graph_module.CHECKPOINT_DB_PATH = original_path


class SupervisorInlineApprovalTests(unittest.TestCase):
    def test_interpret_inline_approval_yes(self):
        supervisor = AgentSupervisor.__new__(AgentSupervisor)
        self.assertTrue(supervisor._interpret_inline_approval_text("是"))
        self.assertTrue(supervisor._interpret_inline_approval_text("继续"))
        self.assertTrue(supervisor._interpret_inline_approval_text("yes"))

    def test_interpret_inline_approval_reject(self):
        supervisor = AgentSupervisor.__new__(AgentSupervisor)
        self.assertFalse(supervisor._interpret_inline_approval_text("取消"))
        self.assertFalse(supervisor._interpret_inline_approval_text("拒绝"))
        self.assertFalse(supervisor._interpret_inline_approval_text("no"))

    def test_interpret_inline_approval_unrelated_message(self):
        supervisor = AgentSupervisor.__new__(AgentSupervisor)
        self.assertIsNone(supervisor._interpret_inline_approval_text("？说中文啊"))


class CreateNoteToolFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_create_note_allows_missing_content_with_fallback(self):
        from agent.tools import create_note
        with patch(
            "agent.tools.note_service.create_note",
            new=AsyncMock(return_value={"id": "note_mock_1"}),
        ):
            result = await create_note.ainvoke({"title": "测试空内容创建", "category_id": ""})
        self.assertIn("Successfully created note", result)


if __name__ == "__main__":
    unittest.main()
