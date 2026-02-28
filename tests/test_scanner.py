import pytest
from pathlib import Path
from reqtrace.scanner import scan_file, scan_directory

def test_scan_file_regex(tmp_path):
    # Create a dummy source file
    src_file = tmp_path / "dummy.py"
    src_file.write_text('''
def my_func():
    # @trace: REQ-001
    pass

def my_func_partial():
    # @trace: REQ-002 (45%)
    # @trace: REQ-003( 100 %)  # Spaces should be tolerated
    return True
''')

    matches = scan_file(src_file)
    assert len(matches) == 3
    
    assert matches[0].req_id == "REQ-001"
    assert matches[0].percentage is None
    assert matches[0].line_number == 3
    
    assert matches[1].req_id == "REQ-002"
    assert matches[1].percentage == 45
    assert matches[1].line_number == 7

    assert matches[2].req_id == "REQ-003"
    assert matches[2].percentage == 100
    assert matches[2].line_number == 8

def test_scan_directory_respects_gitignore(tmp_path):
    # Setup directory structure
    (tmp_path / "src").mkdir()
    (tmp_path / ".git").mkdir()
    
    # Valid file
    valid_file = tmp_path / "src" / "main.py"
    valid_file.write_text("# @trace: REQ-VALID")
    
    # Ignored by default hidden rule
    git_file = tmp_path / ".git" / "config"
    git_file.write_text("# @trace: REQ-INVALID")
    
    # Ignored by custom .gitignore
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("ignored_dir/\n")
    
    (tmp_path / "ignored_dir").mkdir()
    ignored_file = tmp_path / "ignored_dir" / "secret.py"
    ignored_file.write_text("# @trace: REQ-INVALID2")
    
    matches = scan_directory(tmp_path)
    
    assert len(matches) == 1
    assert matches[0].req_id == "REQ-VALID"
