"""
Data models for reqtrace requirements and traces.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional


@dataclass
class Requirement:
    """A defined project requirement."""

    id: str
    title: str
    description: str = ""
    derived_from: List[str] = field(default_factory=list)


@dataclass
class TraceMatch:
    """A trace tag found within the source code."""

    file_path: str
    line_number: int
    req_id: str
    percentage: Optional[int] = None
    hash: Optional[str] = None

    def __hash__(self):
        return hash((self.file_path, self.line_number, self.req_id, self.percentage, self.hash))

    def __eq__(self, other):
        if not isinstance(other, TraceMatch):
            return False
        return (
            self.file_path == other.file_path
            and self.line_number == other.line_number
            and self.req_id == other.req_id
            and self.percentage == other.percentage
            and self.hash == other.hash
        )


class RequirementIndex:
    """An index of all loaded requirements."""

    def __init__(self):
        self.requirements: Dict[str, Requirement] = {}

    def add(self, req: Requirement):
        """Adds a requirement to the index."""
        if req.id in self.requirements:
            raise ValueError(f"Requirement with id '{req.id}' already exists.")
        self.requirements[req.id] = req

    def get(self, req_id: str) -> Optional[Requirement]:
        """Gets a requirement by its ID."""
        return self.requirements.get(req_id)

    def validate_graph(self):
        """Validates that all parent IDs exist and there are no cyclic dependencies."""
        # 1. Check for missing parents
        for req in self.requirements.values():
            for parent_id in req.derived_from:
                if parent_id not in self.requirements:
                    raise ValueError(f"Requirement '{req.id}' derives from unknown requirement '{parent_id}'")

        # 2. Check for cycles using DFS
        visited = set()
        recursion_stack = set()

        def dfs(req_id: str):
            visited.add(req_id)
            recursion_stack.add(req_id)

            req = self.requirements[req_id]
            for parent_id in req.derived_from:
                if parent_id not in visited:
                    dfs(parent_id)
                elif parent_id in recursion_stack:
                    raise ValueError(f"Cyclic dependency detected involving requirement '{parent_id}'")

            recursion_stack.remove(req_id)

        for req_id in self.requirements:
            if req_id not in visited:
                dfs(req_id)
