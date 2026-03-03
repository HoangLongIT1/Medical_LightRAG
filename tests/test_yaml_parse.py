from unittest.mock import patch
from nodes import ComposeAnswer


def test_compose_answer_invalid_yaml_returns_fallback():
    node = ComposeAnswer()
    inputs = ("bác sĩ", "Câu hỏi?", [], True, 0.0, [])
    with patch("nodes.call_llm", return_value="invalid response"):
        result = node.exec(inputs)
    assert result["final"] == "Bạn quan tâm đến nội dung nào?"
    assert result["clarify_questions"] == []
    assert result["need_clarify"] is True
