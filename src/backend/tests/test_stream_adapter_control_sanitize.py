from agent.stream_adapter import _is_internal_control_text, _sanitize_user_visible_text


def test_sanitize_strips_prefixed_control_labels():
    text = "DENY_WRITE该笔记保持原文。"
    assert _sanitize_user_visible_text(text) == "该笔记保持原文。"


def test_sanitize_strips_repeated_control_labels():
    text = "_WRITE_WRITE已将笔记分类到工作。"
    assert _sanitize_user_visible_text(text) == "已将笔记分类到工作。"


def test_sanitize_strips_escaped_control_prefix():
    text = "\\_WRITE已将笔记分类到工作。"
    assert _sanitize_user_visible_text(text) == "已将笔记分类到工作。"


def test_internal_control_detection_for_stitched_tokens():
    assert _is_internal_control_text("_WRITE_WRITE")
    assert _is_internal_control_text("DENY_WRITE_WRITE")
    assert _is_internal_control_text("ALLOW_WRITE:")


def test_internal_control_detection_does_not_swallow_normal_text():
    assert not _is_internal_control_text("已将笔记分类到工作。")


def test_sanitize_strips_fullwidth_underscore_and_crlf():
    text = "＿WRITE\r\n＿WRITE_WRITE已将笔记分类到工作。"
    assert _sanitize_user_visible_text(text) == "已将笔记分类到工作。"
