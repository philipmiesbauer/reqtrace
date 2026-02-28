"""
Git integration for extracting metadata from source control.
"""
import subprocess
from dataclasses import dataclass
from typing import Optional, List, Dict
from pathlib import Path


@dataclass
class GitMetadata:
    """Metadata about a specific line or block of code from Git."""

    author: str
    timestamp: int  # Unix timestamp


def _run_git(args: List[str], cwd: Optional[Path] = None) -> str:
    """Helper to run git commands and return output."""
    try:
        result = subprocess.run(["git"] + args, capture_output=True, text=True, check=True, cwd=cwd)
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


def get_line_metadata(filepath: Path, line_number: int) -> Optional[GitMetadata]:
    """
    Gets the latest git metadata (author and timestamp) for a specific line.
    Equivalent to the 'last changed' information.
    """
    # git blame --porcelain -L line,line filepath
    output = _run_git(["blame", "--porcelain", "-L", f"{line_number},{line_number}", str(filepath)])
    if not output:
        return None

    lines = output.splitlines()
    data: Dict[str, str] = {}
    for line in lines:
        if line.startswith("author "):
            data["author"] = line[7:]
        elif line.startswith("author-time "):
            data["timestamp"] = line[12:]

    if "author" in data and "timestamp" in data:
        return GitMetadata(author=data["author"], timestamp=int(data["timestamp"]))

    return None


def get_file_first_commit(filepath: Path) -> Optional[GitMetadata]:
    """
    Gets the metadata for the very first commit of a file.
    Gives a rough 'written' date for requirements.
    """
    # git log --reverse --format="%at %an" --limit 1 -- filepath
    output = _run_git(["log", "--reverse", "--format=%at %an", "-n", "1", "--", str(filepath)])
    if not output:
        return None

    parts = output.strip().split(" ", 1)
    if len(parts) == 2:
        return GitMetadata(author=parts[1], timestamp=int(parts[0]))

    return None


def get_line_first_commit(filepath: Path, line_number: int) -> Optional[GitMetadata]:
    """
    Tries to find the first commit that introduced a specific line.
    Uses git log -L which can be slow but accurate for history.
    """
    # git log -L <start>,<end>:<file> --reverse --format="%at %an" -n 1
    # Note: -L is 1-indexed
    output = _run_git(["log", f"-L{line_number},{line_number}:{filepath}", "--reverse", "--format=%at %an", "-n", "1"])
    if not output:
        return None

    parts = output.strip().split(" ", 1)
    if len(parts) == 2:
        return GitMetadata(author=parts[1], timestamp=int(parts[0]))

    return None
