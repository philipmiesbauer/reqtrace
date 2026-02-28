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
    commit_hash: Optional[str] = None
    commit_subject: Optional[str] = None


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
    commit_hash = None
    if lines and len(lines[0]) >= 40:
        commit_hash = lines[0].split(" ")[0]

    for line in lines:
        if line.startswith("author "):
            data["author"] = line[7:]
        elif line.startswith("author-time "):
            data["timestamp"] = line[12:]
        elif line.startswith("summary "):
            data["subject"] = line[8:]

    if "author" in data and "timestamp" in data:
        return GitMetadata(
            author=data["author"], timestamp=int(data["timestamp"]), commit_hash=commit_hash, commit_subject=data.get("subject")
        )

    return None


def get_file_first_commit(filepath: Path) -> Optional[GitMetadata]:
    """
    Gets the metadata for the very first commit of a file.
    Gives a rough 'written' date for requirements.
    """
    # git log --reverse --format="%at %an%n%H%n%s" --limit 1 -- filepath
    output = _run_git(["log", "--reverse", "--format=%at %an%n%H%n%s", "-n", "1", "--", str(filepath)])
    if not output:
        return None

    lines = output.strip().split("\n")
    if len(lines) >= 3:
        parts = lines[0].split(" ", 1)
        if len(parts) == 2:
            return GitMetadata(author=parts[1], timestamp=int(parts[0]), commit_hash=lines[1], commit_subject=lines[2])

    return None


def get_line_first_commit(filepath: Path, line_number: int) -> Optional[GitMetadata]:
    """
    Tries to find the first commit that introduced a specific line.
    Uses git log -L which can be slow but accurate for history.
    """
    # git log -L <start>,<end>:<file> --reverse --format="%at %an%n%H%n%s" -n 1
    # Note: -L is 1-indexed
    output = _run_git(["log", f"-L{line_number},{line_number}:{filepath}", "--reverse", "--format=%at %an%n%H%n%s", "-n", "1"])
    if not output:
        return None

    # git log -L also outputs the diff, but the format string outputs the requested fields first
    lines = output.strip().split("\n")
    if len(lines) >= 3:
        parts = lines[0].split(" ", 1)
        if len(parts) == 2:
            return GitMetadata(author=parts[1], timestamp=int(parts[0]), commit_hash=lines[1], commit_subject=lines[2])

    return None


def get_range_commits(filepath: Path, line_start: int, line_end: int) -> List[GitMetadata]:
    """
    Finds all commits that modify a specific range of lines.
    Uses git log -L format to extract all history of the block.
    """
    output = _run_git(["log", f"-L{line_start},{line_end}:{filepath}", "--format=COMMIT|%at|%an|%H|%s"])
    if not output:
        return []

    history = []
    lines = output.strip().split("\n")
    for line in lines:
        if line.startswith("COMMIT|"):
            parts = line.split("|", 4)
            if len(parts) == 5:
                _, timestamp_str, author, commit_hash, subject = parts
                history.append(GitMetadata(author=author, timestamp=int(timestamp_str), commit_hash=commit_hash, commit_subject=subject))

    return history
