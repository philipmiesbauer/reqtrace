"""
Basic tests for reqtrace package initialization.
"""
import reqtrace  # pylint: disable=import-error


def test_basic_import():
    """Verify that reqtrace is importable and has a version."""
    assert isinstance(reqtrace.__version__, str)
    assert len(reqtrace.__version__) > 0
