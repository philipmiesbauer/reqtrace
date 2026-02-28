from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .models import RequirementIndex, TraceMatch

@dataclass
class RequirementCoverage:
    req_id: str
    is_implemented: bool
    total_percentage: int
    matches: List[TraceMatch] = field(default_factory=list)

@dataclass
class CoverageReport:
    total_requirements: int
    implemented_requirements: int
    partial_requirements: int
    missing_requirements: int
    coverage_details: Dict[str, RequirementCoverage] = field(default_factory=dict)
    unmatched_traces: List[TraceMatch] = field(default_factory=list)

def calculate_coverage(index: RequirementIndex, traces: List[TraceMatch]) -> CoverageReport:
    """Takes a RequirementIndex and found TraceMatches to calculate the implementation matrix."""
    
    details: Dict[str, RequirementCoverage] = {}
    unmatched: List[TraceMatch] = []
    
    # Initialize the coverage details dictionary with 0% for all known requirements
    for req_id in index.requirements:
        details[req_id] = RequirementCoverage(
            req_id=req_id,
            is_implemented=False,
            total_percentage=0,
            matches=[]
        )
        
    # Apply traces to their corresponding requirements
    for trace in traces:
        if trace.req_id in details:
            target = details[trace.req_id]
            target.matches.append(trace)
            
            # If percentage is None, assume 100% (the whole thing is implemented here)
            # Otherwise add up the specific percentage
            added_pct = trace.percentage if trace.percentage is not None else 100
            target.total_percentage += added_pct
        else:
            # We found a tag in the source code pointing to a requirement that isn't defined
            unmatched.append(trace)
            
    # Calculate final status
    implemented_count = 0
    partial_count = 0
    missing_count = 0
    
    for req_id, cov in details.items():
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
        unmatched_traces=unmatched
    )
