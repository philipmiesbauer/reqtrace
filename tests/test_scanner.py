"""
Tests for source code requirement tag scanning.
"""
from reqtrace.scanner import scan_file, scan_directory


def test_scan_file_regex(tmp_path):
    """Verify the trace tag matching regex engine extracts IDs and percentages."""
    # Create a dummy source file
    src_file = tmp_path / "dummy.py"
    src_file.write_text(
        """
def my_func():
    # @trace-start: REQ-001
    pass
    # @trace-end: REQ-001

def my_func_partial():
    # @trace-start: REQ-002 (45%)
    # @trace-start: REQ-003( 100 %)  # Spaces should be tolerated
    return True
    # @trace-end: REQ-002
    # @trace-end: REQ-003
"""
    )

    matches, total_lines, is_disabled = scan_file(src_file)
    assert len(matches) == 3
    assert total_lines == 12
    assert not is_disabled

    assert matches[0].req_id == "REQ-001"
    assert matches[0].percentage is None
    assert matches[0].line_start == 3
    assert matches[0].line_end == 5

    assert matches[1].req_id == "REQ-002"
    assert matches[1].percentage == 45
    assert matches[1].line_start == 8
    assert matches[1].line_end == 11

    assert matches[2].req_id == "REQ-003"
    assert matches[2].percentage == 100
    assert matches[2].line_start == 9
    assert matches[2].line_end == 12


def test_scan_disabled_file(tmp_path):
    """Verify that @trace: disable triggers the disabled flag."""
    src_file = tmp_path / "disabled.py"
    src_file.write_text(
        """
# @trace: disable
def ignore_me():
    # @trace-start: REQ-001
    pass
    # @trace-end: REQ-001
"""
    )

    matches, total_lines, is_disabled = scan_file(src_file)
    assert len(matches) == 0
    assert total_lines == 6
    assert is_disabled


def test_scan_directory_respects_gitignore(tmp_path):
    """Verify directory scanner correctly filters pathspec and gitignores."""
    # Setup directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()

    # Valid file
    valid_file = tmp_path / "src" / "main.py"
    valid_file.write_text("# @trace-start: REQ-VALID\n# @trace-end: REQ-VALID\n")

    # Ignored by default hidden rule
    git_file = tmp_path / ".git" / "config"
    git_file.write_text("# @trace-start: REQ-INVALID\n# @trace-end: REQ-INVALID\n")

    # Ignored by custom .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("ignored_dir/\n")

    (tmp_path / "ignored_dir").mkdir()
    ignored_file = tmp_path / "ignored_dir" / "secret.py"
    ignored_file.write_text("# @trace-start: REQ-INVALID2\n# @trace-end: REQ-INVALID2\n")

    matches, file_lines = scan_directory(tmp_path)

    assert len(matches) == 1
    assert len(file_lines) == 1
    assert str(valid_file) in file_lines
    assert file_lines[str(valid_file)] == (2, False)
    assert matches[0].req_id == "REQ-VALID"
