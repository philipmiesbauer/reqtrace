"""
Basic tests for reqtrace package initialization.
"""
import reqtrace


def test_basic_import():
    """Verify that reqtrace is importable and has a version."""
    assert reqtrace.__version__ == "0.1.0"
