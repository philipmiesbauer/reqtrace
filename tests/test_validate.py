"""
Tests for reqtrace-validate (schema validation of .rqtr files).
"""
import textwrap
from pathlib import Path


from reqtrace.validate.validate_cli import validate_file


def _write_rqtr(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "test.rqtr"
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def test_valid_file(tmp_path):
    """A well-formed .rqtr file passes validation."""
    path = _write_rqtr(
        tmp_path,
        """\
        - id: SYS-001
          title: System Requirement
          description: Some description
          derived_from: []
        - id: REQ-001
          title: Child Requirement
          derived_from: [SYS-001]
        """,
    )
    errors = validate_file(path)
    assert not errors, f"Expected no errors, got: {errors}"


def test_missing_id(tmp_path):
    """A requirement missing 'id' should fail validation."""
    path = _write_rqtr(
        tmp_path,
        """\
        - title: No ID here
        """,
    )
    errors = validate_file(path)
    assert any("id" in e for e in errors), f"Expected 'id' error, got: {errors}"


def test_missing_title(tmp_path):
    """A requirement missing 'title' should fail validation."""
    path = _write_rqtr(
        tmp_path,
        """\
        - id: REQ-001
        """,
    )
    errors = validate_file(path)
    assert any("title" in e for e in errors), f"Expected 'title' error, got: {errors}"


def test_wrong_type_top_level(tmp_path):
    """A file with a dict at the top level (instead of a list) should fail."""
    path = _write_rqtr(
        tmp_path,
        """\
        id: REQ-001
        title: Should be a list
        """,
    )
    errors = validate_file(path)
    assert len(errors) > 0, "Expected errors for non-list top-level"


def test_derived_from_wrong_type(tmp_path):
    """derived_from must be an array, not a plain string."""
    path = _write_rqtr(
        tmp_path,
        """\
        - id: REQ-001
          title: Bad derived_from
          derived_from: SYS-001
        """,
    )
    errors = validate_file(path)
    assert any("derived_from" in e for e in errors), f"Expected derived_from type error, got: {errors}"


def test_file_not_found(tmp_path):
    """A missing file should return a 'File not found' error."""
    path = tmp_path / "nonexistent.rqtr"
    errors = validate_file(path)
    assert any("not found" in e.lower() for e in errors), f"Expected file-not-found error, got: {errors}"


def test_invalid_yaml(tmp_path):
    """A file with YAML syntax errors should return a parse error."""
    path = tmp_path / "bad.rqtr"
    path.write_text("- id: [unclosed bracket\n", encoding="utf-8")
    errors = validate_file(path)
    assert any("yaml" in e.lower() or "parse" in e.lower() for e in errors), f"Expected YAML error, got: {errors}"
