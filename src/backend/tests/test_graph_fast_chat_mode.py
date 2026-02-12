from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.graph import NoteAgentGraph


class _FakeLLM:
    def __init__(self):
        self.last_messages = None

    def invoke(self, messages):
        self.last_messages = messages
        return AIMessage(content="ok")


def _build_graph_with_fake_llm():
    graph = NoteAgentGraph.__new__(NoteAgentGraph)
    graph.llm = _FakeLLM()
    return graph


def _system_contents(messages):
    return [m.content for m in messages if isinstance(m, SystemMessage)]


def test_fast_chat_injects_ask_mode_guardrails():
    graph = _build_graph_with_fake_llm()
    state = {
        "messages": [HumanMessage(content="当前是什么模式？")],
        "agent_mode": "ask",
    }

    result = graph._fast_chat_node(state)

    assert result["messages"][0].content == "ok"
    sys_msgs = _system_contents(graph.llm.last_messages)
    assert any("ASK MODE" in msg for msg in sys_msgs)
    assert any("read-only" in msg.lower() for msg in sys_msgs)


def test_fast_chat_injects_agent_mode_capability_context():
    graph = _build_graph_with_fake_llm()
    state = {
        "messages": [HumanMessage(content="what mode are you in?")],
        "agent_mode": "agent",
    }

    result = graph._fast_chat_node(state)

    assert result["messages"][0].content == "ok"
    sys_msgs = _system_contents(graph.llm.last_messages)
    assert any("AGENT MODE" in msg for msg in sys_msgs)


def test_router_prefers_chat_for_image_input_without_write_intent():
    graph = _build_graph_with_fake_llm()
    state = {
        "messages": [
            HumanMessage(content=[
                {"type": "text", "text": "读取这张图片的内容"},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
            ])
        ],
        "use_knowledge": False,
    }

    result = graph._router_node(state)

    assert result["intent"] == "CHAT"
