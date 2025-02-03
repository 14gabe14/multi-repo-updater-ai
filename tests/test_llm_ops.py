import pytest
from unittest.mock import patch, MagicMock
from llm_ops import get_llm_suggestion, validate_python_syntax, apply_llm_changes

def test_get_llm_suggestion_success():
    """
    Test that get_llm_suggestion returns the content from the mocked LLM response.
    """
    with patch("openai.resources.chat.Completions.create") as mock_create:
        mock_create.return_value = {
            "choices": [{"message": {"content": "new file content"}}]
        }
        result = get_llm_suggestion("old content", "update dependency")
        assert result == "new file content"

def test_get_llm_suggestion_retry():
    """
    Test the retry logic when the LLM call fails initially.
    """
    with patch("openai.resources.chat.Completions.create", side_effect=[Exception("API error"), {"choices": [{"message": {"content": "retry content"}}]}]):
        result = get_llm_suggestion("old content", "prompt", max_retries=2)
        assert result == "retry content"

def test_validate_python_syntax_valid():
    code_snippet = "import sys\nprint(sys.version)\n"
    assert validate_python_syntax(code_snippet) is True

def test_validate_python_syntax_invalid():
    code_snippet = "def foo(:\n  pass"
    assert validate_python_syntax(code_snippet) is False

def test_apply_llm_changes_valid(tmp_path):
    """
    If LLM provides valid Python, it should overwrite the file.
    """
    file_path = tmp_path / "test.py"
    file_path.write_text("original code")

    apply_llm_changes("original code", "print('new code')", str(file_path))
    new_content = file_path.read_text()
    assert "new code" in new_content

def test_apply_llm_changes_invalid_python(tmp_path):
    """
    If LLM suggestion is invalid Python, the file should remain unchanged.
    """
    file_path = tmp_path / "test.py"
    file_path.write_text("original code")

    apply_llm_changes("original code", "def foo(:", str(file_path))
    new_content = file_path.read_text()
    assert "original code" in new_content
    assert "def foo(" not in new_content
