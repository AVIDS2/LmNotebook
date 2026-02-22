from agent.graph import NoteAgentGraph


def _graph_stub() -> NoteAgentGraph:
    graph = NoteAgentGraph.__new__(NoteAgentGraph)
    graph._get_last_user_text = lambda history: "整理当前笔记格式"
    graph._classify_write_authorization = lambda history: False
    return graph


def test_manual_review_mode_does_not_preemptively_deny_write():
    graph = _graph_stub()
    state = {
        "agent_mode": "agent",
        "auto_accept_writes": False,
        "write_authorized": False,
        "messages": [],
    }

    decision = graph._evaluate_tool_policy(
        state=state,
        tool_name="update_note",
        tool_args={"note_id": "1", "instruction": "整理"},
        history=[],
    )

    assert decision["action"] == "allow"
    assert decision["code"] == "manual_review_required"


def test_auto_accept_mode_still_denies_without_explicit_write_auth():
    graph = _graph_stub()
    state = {
        "agent_mode": "agent",
        "auto_accept_writes": True,
        "write_authorized": False,
        "messages": [],
    }

    decision = graph._evaluate_tool_policy(
        state=state,
        tool_name="update_note",
        tool_args={"note_id": "1", "instruction": "整理"},
        history=[],
    )

    assert decision["action"] == "deny"
    assert decision["code"] == "semantic_deny_write"


def test_status_node_uses_blocked_marker_on_tool_failure():
    graph = _graph_stub()
    state = {"last_tool_name": "update_note", "last_tool_success": False}

    result = graph._status_node(state)
    msg = result["messages"][0]

    assert getattr(msg, "content", "") == "[Blocked] update_note"


def test_create_note_denied_for_category_feedback_without_explicit_create():
    graph = _graph_stub()
    graph._get_last_user_text = lambda history: "你并没有归类到工作呀"
    state = {
        "agent_mode": "agent",
        "auto_accept_writes": True,
        "write_authorized": True,
        "messages": [],
    }

    decision = graph._evaluate_tool_policy(
        state=state,
        tool_name="create_note",
        tool_args={"title": "宇树科技的发展史", "content": "x"},
        history=[],
    )

    assert decision["action"] == "deny"
    assert decision["code"] == "duplicate_create_blocked_for_category_feedback"


def test_create_note_allowed_when_user_explicitly_requests_new_creation():
    graph = _graph_stub()
    graph._get_last_user_text = lambda history: "请重新创建一篇笔记并归类到工作"
    state = {
        "agent_mode": "agent",
        "auto_accept_writes": True,
        "write_authorized": True,
        "messages": [],
    }

    decision = graph._evaluate_tool_policy(
        state=state,
        tool_name="create_note",
        tool_args={"title": "宇树科技的发展史", "content": "x"},
        history=[],
    )

    assert decision["action"] == "allow"
    assert decision["code"] == "semantic_allow_write"
