"""
Logic for calculating the requirement coverage matrix.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from .models import RequirementIndex, TraceMatch


@dataclass
class RequirementCoverage:
    """Holds calculated implementation details for a single requirement."""

    req_id: str
    is_implemented: bool
    total_percentage: int
    matches: List[TraceMatch] = field(default_factory=list)


@dataclass
class CoverageReport:
    """The final calculated matrix report for the entire run."""

    total_requirements: int
    implemented_requirements: int
    partial_requirements: int
    missing_requirements: int
    coverage_details: Dict[str, RequirementCoverage] = field(default_factory=dict)
    unmatched_traces: List[TraceMatch] = field(default_factory=list)


def _apply_direct_traces(index: RequirementIndex, traces: List[TraceMatch]) -> Tuple[Dict[str, RequirementCoverage], List[TraceMatch]]:
    details: Dict[str, RequirementCoverage] = {}
    unmatched: List[TraceMatch] = []

    for req_id in index.requirements:
        details[req_id] = RequirementCoverage(req_id=req_id, is_implemented=False, total_percentage=0, matches=[])

    for trace in traces:
        if trace.req_id in details:
            target = details[trace.req_id]
            target.matches.append(trace)
            added_pct = trace.percentage if trace.percentage is not None else 100
            target.total_percentage += added_pct
        else:
            unmatched.append(trace)

    return details, unmatched


def _build_reverse_mapping(index: RequirementIndex) -> Dict[str, List[str]]:
    children: Dict[str, List[str]] = {req_id: [] for req_id in index.requirements}
    for req in index.requirements.values():
        for parent_id in req.derived_from:
            if parent_id in children:
                children[parent_id].append(req.id)
    return children


# @trace-start: REQ-GRAPH
def _calculate_rollups(index: RequirementIndex, details: Dict[str, RequirementCoverage]) -> None:
    children = _build_reverse_mapping(index)
    computed_totals: Dict[str, int] = {}

    def compute_total(req_id: str) -> int:
        if req_id in computed_totals:
            return computed_totals[req_id]

        direct_pct = details[req_id].total_percentage
        child_ids = children[req_id]

        if not child_ids:
            rollup = 0
            full_total = direct_pct
        else:
            rollup_sum = sum(min(100, compute_total(cid)) for cid in child_ids)
            rollup = rollup_sum // len(child_ids)

            if direct_pct == 0:
                full_total = rollup
            else:
                # If children exist, direct implementation accounts for at most 50%,
                # and the children account for the other 50%.
                direct_contribution = min(100, direct_pct) // 2
                child_contribution = rollup // 2
                full_total = direct_contribution + child_contribution

        computed_totals[req_id] = full_total
        details[req_id].total_percentage = full_total
        return full_total

    for req_id in index.requirements:
        compute_total(req_id)


# @trace-end: REQ-GRAPH


def _build_report(index: RequirementIndex, details: Dict[str, RequirementCoverage], unmatched: List[TraceMatch]) -> CoverageReport:
    implemented_count = 0
    partial_count = 0
    missing_count = 0

    for cov in details.values():
        if cov.total_percentage >= 100:
            cov.is_implemented = True
            implemented_count += 1
        elif cov.total_percentage > 0:
            partial_count += 1
        else:
            missing_count += 1

    return CoverageReport(
        total_requirements=len(index.requirements),
        implemented_requirements=implemented_count,
        partial_requirements=partial_count,
        missing_requirements=missing_count,
        coverage_details=details,
        unmatched_traces=unmatched,
    )


def calculate_coverage(index: RequirementIndex, traces: List[TraceMatch]) -> CoverageReport:
    """Takes a RequirementIndex and found TraceMatches to calculate the implementation matrix."""
    details, unmatched = _apply_direct_traces(index, traces)
    _calculate_rollups(index, details)
    return _build_report(index, details, unmatched)
