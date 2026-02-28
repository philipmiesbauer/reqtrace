import re
import os
from pathlib import Path
from typing import List, Union
import pathspec

from .models import TraceMatch

# Matches e.g. "@trace: REQ-123" or "@trace: REQ-123 (50%)"
# We match "@trace:[spaces][ID][spaces][optional(Number%)]"
TAG_PATTERN = re.compile(r'@trace:\s*([A-Za-z0-9_-]+)(?:\s*\(\s*(\d+)\s*%\s*\))?')

def scan_file(filepath: Union[str, Path]) -> List[TraceMatch]:
    """Scans a single text file for requirement trace tags."""
    # @trace: REQ-SCAN-REGEX
    filepath = Path(filepath)
    matches = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, start=1):
                for match in TAG_PATTERN.finditer(line):
                    req_id = match.group(1)
                    pct_str = match.group(2)
                    percentage = int(pct_str) if pct_str else None
                    
                    matches.append(TraceMatch(
                        file_path=str(filepath),
                        line_number=line_no,
                        req_id=req_id,
                        percentage=percentage
                    ))
    except UnicodeDecodeError:
        # Ignore binary files or files with strange encodings
        pass
        
    return matches

def _get_ignore_spec(directory: Path) -> pathspec.PathSpec:
    """Reads .gitignore if present and returns a PathSpec object."""
    gitignore_path = directory / '.gitignore'
    patterns = []
    
    # Always ignore standard hidden dirs and binary/cache dirs
    patterns.extend(['.git/', '__pycache__/', '*.pyc', '*.pyo', '.pytest_cache/', 'site/'])
    
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            patterns.extend(f.readlines())
            
    return pathspec.PathSpec.from_lines('gitignore', patterns)

def scan_directory(directory: Union[str, Path]) -> List[TraceMatch]:
    """Recursively scans a directory for trace tags, respecting .gitignore."""
    # @trace: REQ-SCAN-DIR
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"'{directory}' is not a directory")
        
    spec = _get_ignore_spec(directory)
    all_matches = []
    
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)
        
        # Filter directories in-place based on pathspec
        # We need the path relative to the base directory
        dirs[:] = [d for d in dirs if not spec.match_file(str((root_path / d).relative_to(directory)) + '/')]
        
        for file in files:
            file_rel_path = str((root_path / file).relative_to(directory))
            if not spec.match_file(file_rel_path):
                filepath = root_path / file
                all_matches.extend(scan_file(filepath))
                
    return all_matches
