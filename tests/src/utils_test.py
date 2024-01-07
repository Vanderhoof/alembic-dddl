import pytest

from alembic_dddl.src.utils import escape_quotes, ensure_dir


@pytest.mark.parametrize(
    "input_text, expected_output",
    [
        ("O'Neill", "O\\'Neill"),  # Test with single quotes
        ("Hello World", "Hello World"),  # Test with no quotes
        ("", ""),  # Test with empty string
        ("''''", "\\'\\'\\'\\'"),  # Test with only single quotes
        ("It's 5 o'clock", "It\\'s 5 o\\'clock"),  # Test with mixed characters
        ("O\\'Neill", "O\\\\'Neill"),  # Test with already escaped quotes
    ],
)
def test_escape_quotes(input_text, expected_output):
    assert escape_quotes(input_text) == expected_output


def test_ensure_dir_creates_directory(tmp_path):
    new_dir = tmp_path / "new_dir"
    ensure_dir(str(new_dir))
    assert new_dir.is_dir()


def test_ensure_dir_existing_directory(tmp_path):
    existing_dir = tmp_path / "existing_dir"
    existing_dir.mkdir()
    ensure_dir(str(existing_dir))
    assert existing_dir.is_dir()
