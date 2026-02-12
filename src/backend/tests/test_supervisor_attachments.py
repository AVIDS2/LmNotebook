from langchain_core.messages import HumanMessage

from agent.supervisor import AgentSupervisor


def _supervisor_stub() -> AgentSupervisor:
    return AgentSupervisor.__new__(AgentSupervisor)


def test_build_user_message_without_attachments_returns_plain_text():
    supervisor = _supervisor_stub()

    message, attachment_context = supervisor._build_user_message_and_attachment_context(
        message="hello",
        attachments=None,
    )

    assert isinstance(message, HumanMessage)
    assert message.content == "hello"
    assert attachment_context is None


def test_build_user_message_with_image_and_file_generates_multimodal_payload():
    supervisor = _supervisor_stub()

    message, attachment_context = supervisor._build_user_message_and_attachment_context(
        message="analyze this",
        attachments=[
            {
                "kind": "image",
                "name": "screen.png",
                "mime_type": "image/png",
                "size_bytes": 128,
                "data_url": "data:image/png;base64,abc",
            },
            {
                "kind": "file",
                "name": "notes.md",
                "mime_type": "text/markdown",
                "size_bytes": 64,
                "text_content": "# title\nbody",
            },
        ],
    )

    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, list)
    assert any(block.get("type") == "image_url" for block in message.content)
    assert attachment_context is not None
    assert "notes.md" in attachment_context
    assert "# title" in attachment_context
