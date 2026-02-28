"""
Parser for loading YAML requirements files.
"""
from pathlib import Path
from typing import List, Dict, Any, Union
import yaml

from .models import Requirement, RequirementIndex


# pylint: disable=too-many-ancestors
class LineLoader(yaml.SafeLoader):
    """Custom YAML loader that attaches line numbers to dictionaries."""

    def construct_mapping(self, node, deep=False):
        mapping = super().construct_mapping(node, deep=deep)
        mapping["__line__"] = node.start_mark.line + 1
        return mapping


def load_yaml(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """Loads a YAML file and returns a list of dictionaries."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f, Loader=LineLoader)

    if not isinstance(data, list):
        raise ValueError(f"Expected a list of requirements in '{filepath}', but got {type(data).__name__}")

    for item in data:
        if isinstance(item, dict):
            item["__file__"] = str(path)

    return data


def parse_requirements(data: List[Dict[str, Any]]) -> RequirementIndex:
    """Parses a list of dictionaries into a validated RequirementIndex."""
    # @trace-start: REQ-PARSE
    index = RequirementIndex()

    for item in data:
        if not isinstance(item, dict):
            raise ValueError(f"Expected a dictionary for requirement, got {type(item).__name__}")

        if "id" not in item:
            raise ValueError("Requirement is missing required field: 'id'")
        if "title" not in item:
            raise ValueError(f"Requirement '{item['id']}' is missing required field: 'title'")

        req = Requirement(
            id=item["id"],
            title=item["title"],
            description=item.get("description", ""),
            derived_from=item.get("derived_from", []),
            file_path=item.get("__file__"),
            line_number=item.get("__line__"),
        )
        index.add(req)

    # Validate the entire graph after loading all items
    index.validate_graph()
    # @trace-end: REQ-PARSE
    return index


def load_requirements_file(filepath: Union[str, Path]) -> RequirementIndex:
    """Convenience function to load a YAML file and return a fully validated RequirementIndex."""
    data = load_yaml(filepath)
    return parse_requirements(data)
