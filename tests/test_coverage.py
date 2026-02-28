"""
Tests for the requirement coverage calculation.
"""
from reqtrace.models import Requirement, RequirementIndex, TraceMatch
from reqtrace.coverage import calculate_coverage


def test_coverage_calculation():
    """Verify that the engine calculates requirement coverage percentage correctly."""
    # Setup dummy Index
    index = RequirementIndex()
    index.add(Requirement(id="REQ-100", title="100% Single match"))
    index.add(Requirement(id="REQ-PARTIAL", title="Partial via sums"))
    index.add(Requirement(id="REQ-MISSING", title="No matches found"))
    index.add(Requirement(id="REQ-OVER", title="More than 100%"))

    # Setup traces manually found in codebase
    traces = [
        # Full implicit implementation
        TraceMatch(file_path="foo.py", line_number=1, req_id="REQ-100"),
        # Partial explicitly summed implementation
        TraceMatch(file_path="foo.py", line_number=5, req_id="REQ-PARTIAL", percentage=20),
        TraceMatch(file_path="bar.py", line_number=10, req_id="REQ-PARTIAL", percentage=30),
        # Over-allocated matches
        TraceMatch(file_path="baz.py", line_number=1, req_id="REQ-OVER", percentage=60),
        TraceMatch(file_path="baz.py", line_number=2, req_id="REQ-OVER", percentage=50),
        # Unknown/Typoed req id tags found in source code
        TraceMatch(file_path="typo.py", line_number=1, req_id="REQ-TYYPO"),
    ]

    report = calculate_coverage(index, traces)

    # Verify overall metrics
    assert report.total_requirements == 4
    assert report.implemented_requirements == 2  # 100 and OVER
    assert report.partial_requirements == 1  # PARTIAL
    assert report.missing_requirements == 1  # MISSING

    # Verify specific traces matched
    assert report.coverage_details["REQ-100"].is_implemented is True
    assert report.coverage_details["REQ-100"].total_percentage == 100

    assert report.coverage_details["REQ-PARTIAL"].is_implemented is False
    assert report.coverage_details["REQ-PARTIAL"].total_percentage == 50
    assert len(report.coverage_details["REQ-PARTIAL"].matches) == 2

    assert report.coverage_details["REQ-MISSING"].is_implemented is False
    assert report.coverage_details["REQ-MISSING"].total_percentage == 0

    assert report.coverage_details["REQ-OVER"].is_implemented is True
    assert report.coverage_details["REQ-OVER"].total_percentage == 110

    # Verify the typo tracer was correctly cached
    assert len(report.unmatched_traces) == 1
    assert report.unmatched_traces[0].req_id == "REQ-TYYPO"
