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
        TraceMatch(file_path="foo.py", line_start=1, line_end=4, req_id="REQ-100"),
        # Partial explicitly summed implementation
        TraceMatch(file_path="foo.py", line_start=5, line_end=9, req_id="REQ-PARTIAL", percentage=20),
        TraceMatch(file_path="bar.py", line_start=10, line_end=15, req_id="REQ-PARTIAL", percentage=30),
        # Over-allocated matches
        TraceMatch(file_path="baz.py", line_start=1, line_end=1, req_id="REQ-OVER", percentage=60),
        TraceMatch(file_path="baz.py", line_start=2, line_end=4, req_id="REQ-OVER", percentage=50),
        # Unknown/Typoed req id tags found in source code
        TraceMatch(file_path="typo.py", line_start=1, line_end=3, req_id="REQ-TYYPO"),
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


def test_coverage_rollup():
    """Verify that requirement coverage rolls up from derived requirements."""
    index = RequirementIndex()
    # P1 has two children, one 100%, one 50%. Expected rollup: 75%
    index.add(Requirement(id="P1", title="Parent 1"))
    index.add(Requirement(id="C1", title="Child 1", derived_from=["P1"]))
    index.add(Requirement(id="C2", title="Child 2", derived_from=["P1"]))

    # P2 has one child with 150%. Expected rollup: 100% (capped at 100% per child)
    index.add(Requirement(id="P2", title="Parent 2"))
    index.add(Requirement(id="C3", title="Child 3", derived_from=["P2"]))

    # P3 has direct coverage (20%) and one child (50%). Expected rollup: 70%
    index.add(Requirement(id="P3", title="Parent 3"))
    index.add(Requirement(id="C4", title="Child 4", derived_from=["P3"]))

    # P4 has direct coverage of 100% but one child with 0%. Expected rollup: 99%
    index.add(Requirement(id="P4", title="Parent 4"))
    index.add(Requirement(id="C5", title="Child 5", derived_from=["P4"]))

    traces = [
        TraceMatch(file_path="foo.py", line_start=1, line_end=1, req_id="C1"),
        TraceMatch(file_path="foo.py", line_start=2, line_end=2, req_id="C2", percentage=50),
        TraceMatch(file_path="foo.py", line_start=3, line_end=3, req_id="C3", percentage=150),
        TraceMatch(file_path="foo.py", line_start=4, line_end=4, req_id="P3", percentage=20),
        TraceMatch(file_path="foo.py", line_start=5, line_end=5, req_id="C4", percentage=50),
        TraceMatch(file_path="foo.py", line_start=6, line_end=6, req_id="P4", percentage=100),
    ]

    report = calculate_coverage(index, traces)

    assert report.coverage_details["C1"].total_percentage == 100
    assert report.coverage_details["C2"].total_percentage == 50
    # P1 has 0% direct, children are (100+50)/2 = 75%. Child contribution is 75 // 2 = 37%
    assert report.coverage_details["P1"].total_percentage == 37

    assert report.coverage_details["C3"].total_percentage == 150
    # P2 has 0% direct, children are min(100, 150) = 100%. Child contribution is 100 // 2 = 50%
    assert report.coverage_details["P2"].total_percentage == 50

    assert report.coverage_details["C4"].total_percentage == 50
    # P3 has 20% direct. Direct contribution = 10%. Children are 50%. Child contribution = 25%. Total = 35%
    assert report.coverage_details["P3"].total_percentage == 35

    assert report.coverage_details["C5"].total_percentage == 0
    # P4 has 100% direct. Direct contribution = 50%. Children are 0%. Child contribution = 0%. Total = 50%
    assert report.coverage_details["P4"].total_percentage == 50
