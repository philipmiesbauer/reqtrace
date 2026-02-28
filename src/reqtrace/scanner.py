"""
Scanner for finding trace tags in source code files.
"""
import re
import os
from pathlib import Path
from typing import List, Union
import pathspec

from .models import TraceMatch

# Matches e.g. "@ trace-start: REQUIRE-123" (ignore the space to avoid false positives)
# or "@ trace-start: REQUIRE-123 (50%)"
START_TAG_PATTERN = re.compile(r"@trace-start:\s*([A-Za-z0-9_-]+)(?:\s*\(\s*(\d+)\s*%\s*\))?")
# Matches e.g. "@ trace-end: REQUIRE-123"
END_TAG_PATTERN = re.compile(r"@trace-end:\s*([A-Za-z0-9_-]+)")


def scan_file(filepath: Union[str, Path]) -> List[TraceMatch]:
    """Scans a single text file for requirement trace tags."""
    # @trace-start: REQ-SCAN-REGEX
    path = Path(filepath)
    matches = []
    open_traces = {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                for match in START_TAG_PATTERN.finditer(line):
                    req_id = match.group(1)
                    pct_str = match.group(2)
                    percentage = int(pct_str) if pct_str else None
                    open_traces[req_id] = (line_no, percentage)

                for match in END_TAG_PATTERN.finditer(line):
                    req_id = match.group(1)
                    if req_id in open_traces:
                        start_line, percentage = open_traces.pop(req_id)
                        matches.append(
                            TraceMatch(
                                file_path=str(path),
                                line_start=start_line,
                                line_end=line_no,
                                req_id=req_id,
                                percentage=percentage,
                            )
                        )
    except UnicodeDecodeError:
        # Ignore binary files or files with strange encodings
        pass

    # @trace-end: REQ-SCAN-REGEX
    return matches


def _get_ignore_spec(directory: Path) -> pathspec.PathSpec:
    """Reads .gitignore if present and returns a PathSpec object."""
    patterns = []

    # Always ignore standard hidden dirs, caches, and build folders
    patterns.extend(
        [
            ".git/",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            ".pytest_cache/",
            "site/",
            "*.egg-info/",
            "*.egg",
        ]
    )

    # Search for .gitignore in the current directory or its parents
    current = directory.resolve()
    gitignore_path = None
    for p in [current, *current.parents]:
        if (p / ".gitignore").exists():
            gitignore_path = p / ".gitignore"
            break

    if gitignore_path:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            patterns.extend(f.readlines())

    return pathspec.PathSpec.from_lines("gitignore", patterns)


def scan_directory(directory: Union[str, Path]) -> List[TraceMatch]:
    """Recursively scans a directory for trace tags, respecting .gitignore."""
    # @trace-start: REQ-SCAN-DIR
    dir_path = Path(directory)
    if not dir_path.is_dir():
        raise ValueError(f"'{dir_path}' is not a directory")

    spec = _get_ignore_spec(dir_path)
    all_matches = []

    for root, dirs, files in os.walk(dir_path):
        root_path = Path(root)

        # Filter directories in-place based on pathspec
        # We need the path relative to the base directory
        dirs[:] = [d for d in dirs if not spec.match_file(str((root_path / d).relative_to(dir_path)) + "/")]

        for file in files:
            file_rel_path = str((root_path / file).relative_to(dir_path))
            if not spec.match_file(file_rel_path):
                filepath = root_path / file
                all_matches.extend(scan_file(filepath))

    # @trace-end: REQ-SCAN-DIR
    return all_matches
