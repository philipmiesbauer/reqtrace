"""
HTML visualization generator for reqtrace reports.
"""
import datetime
import logging
from pathlib import Path
from typing import Optional
from .models import RequirementIndex
from .coverage import CoverageReport
from .git import get_line_metadata, get_line_first_commit

log = logging.getLogger(__name__)


def enrich_metadata(index: RequirementIndex, report: CoverageReport):
    """Enriches requirements and traces with git metadata."""
    log.info("Enriching requirements with git metadata...")
    for req in index.requirements.values():
        if req.file_path and req.line_number:
            path = Path(req.file_path)
            req.last_changed = get_line_metadata(path, req.line_number)
            req.created = get_line_first_commit(path, req.line_number)

    log.info("Enriching traces with git metadata...")
    for cov in report.coverage_details.values():
        for match in cov.matches:
            path = Path(match.file_path)
            match.last_changed = get_line_metadata(path, match.line_number)
            match.first_implemented = get_line_first_commit(path, match.line_number)

    for match in report.unmatched_traces:
        path = Path(match.file_path)
        match.last_changed = get_line_metadata(path, match.line_number)
        match.first_implemented = get_line_first_commit(path, match.line_number)


def _format_date(timestamp: Optional[int]) -> str:
    """Formats a unix timestamp as a human-readable date."""
    if timestamp is None:
        return "Unknown"
    return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")


def generate_html(index: RequirementIndex, report: CoverageReport) -> str:
    """Generates a fancy HTML report string."""
    # pylint: disable=too-many-locals

    css = """
    :root {
        --bg-color: #0b0f19;
        --card-bg: rgba(23, 31, 48, 0.7);
        --text-primary: #f8fafc;
        --text-secondary: #94a3b8;
        --accent-blue: #38bdf8;
        --accent-green: #4ade80;
        --accent-yellow: #fbbf24;
        --accent-red: #f87171;
        --glass-border: rgba(255, 255, 255, 0.08);
    }

    body {
        background-color: var(--bg-color);
        color: var(--text-primary);
        font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
        margin: 0;
        padding: 2rem;
        line-height: 1.6;
    }

    .container {
        max-width: 1100px;
        margin: 0 auto;
    }

    header {
        margin-bottom: 4rem;
        text-align: center;
        padding-top: 2rem;
    }

    h1 {
        font-size: 3rem;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, var(--accent-blue), var(--accent-green));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        font-weight: 800;
    }

    .subtitle {
        color: var(--text-secondary);
        margin-top: 0.5rem;
        font-size: 1.1rem;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1.5rem;
        margin-bottom: 4rem;
    }

    .stat-card {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        padding: 2rem;
        border-radius: 1.25rem;
        text-align: center;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
        position: relative;
        overflow: hidden;
    }

    .stat-card::after {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; height: 3px;
        background: var(--accent-blue);
        opacity: 0.5;
    }

    .stat-value {
        font-size: 2.5rem;
        font-weight: 800;
        display: block;
        margin-bottom: 0.25rem;
    }

    .stat-label {
        color: var(--text-secondary);
        font-size: 0.75rem;
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.1em;
    }

    .req-card {
        background: var(--card-bg);
        backdrop-filter: blur(20px);
        border: 1px solid var(--glass-border);
        border-radius: 1.25rem;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }

    .req-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 1.25rem;
    }

    .req-title-group {
        display: flex;
        flex-direction: column;
    }

    .req-id {
        font-size: 1.5rem;
        font-weight: 800;
        color: var(--accent-blue);
    }

    .req-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    .badge {
        padding: 0.4rem 1rem;
        border-radius: 0.75rem;
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.05em;
    }

    .badge-success { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.2); }
    .badge-warning { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.2); }
    .badge-error { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.2); }

    .progress-container {
        margin: 1.5rem 0;
    }

    .progress-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
    }

    .progress-bar {
        width: 100%;
        height: 10px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        overflow: hidden;
    }

    .progress-fill {
        height: 100%;
        background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
        transition: width 1s ease-out;
    }

    .history-section {
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px solid var(--glass-border);
    }

    .history-title {
        font-size: 0.8rem;
        font-weight: 700;
        text-transform: uppercase;
        color: var(--text-secondary);
        margin-bottom: 1rem;
        letter-spacing: 0.05em;
    }

    .history-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
    }

    .history-item {
        font-size: 0.85rem;
    }

    .history-label {
        display: block;
        color: var(--text-secondary);
        margin-bottom: 0.25rem;
    }

    .history-value {
        font-weight: 600;
        color: var(--text-primary);
    }

    .traces-container {
        margin-top: 1.5rem;
        background: rgba(0, 0, 0, 0.2);
        border-radius: 0.75rem;
        padding: 1rem;
    }

    .trace-item {
        padding: 0.75rem;
        border-bottom: 1px solid var(--glass-border);
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.85rem;
    }

    .trace-item:last-child { border-bottom: none; }

    .trace-info {
        display: flex;
        flex-direction: column;
    }

    .trace-file {
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        color: var(--accent-blue);
    }

    .trace-meta {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    .empty-msg {
        text-align: center;
        color: var(--text-secondary);
        padding: 2rem;
        font-style: italic;
    }
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reqtrace Coverage Report</title>
    <style>{css}</style>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <h1>Reqtrace</h1>
            <div class="subtitle">Requirements Traceability Matrix</div>
            <div style="font-size: 0.85rem; margin-top: 1rem; color: var(--text-secondary)">
                Generated: {_format_date(int(datetime.datetime.now().timestamp()))}
            </div>
        </header>

        <div class="summary-grid">
            <div class="stat-card" style="box-shadow: 0 10px 25px -5px rgba(56, 189, 248, 0.2); border-top: 3px solid var(--accent-blue)">
                <span class="stat-value">{report.total_requirements}</span>
                <span class="stat-label">Requirements</span>
            </div>
            <div class="stat-card" style="box-shadow: 0 10px 25px -5px rgba(74, 222, 128, 0.2); border-top: 3px solid var(--accent-green)">
                <span class="stat-value" style="color: var(--accent-green)">{report.implemented_requirements}</span>
                <span class="stat-label">Full Coverage</span>
            </div>
            <div class="stat-card" style="box-shadow: 0 10px 25px -5px rgba(251, 191, 36, 0.2); border-top: 3px solid var(--accent-yellow)">
                <span class="stat-value" style="color: var(--accent-yellow)">{report.partial_requirements}</span>
                <span class="stat-label">Partial Coverage</span>
            </div>
            <div class="stat-card" style="box-shadow: 0 10px 25px -5px rgba(248, 113, 113, 0.2); border-top: 3px solid var(--accent-red)">
                <span class="stat-value" style="color: var(--accent-red)">{report.missing_requirements}</span>
                <span class="stat-label">Missing</span>
            </div>
        </div>

        <h2 style="margin-bottom: 2rem;">Implementation Matrix</h2>
    """

    # Sort requirements by ID
    sorted_ids = sorted(index.requirements.keys())

    for req_id in sorted_ids:
        req = index.requirements[req_id]
        cov = report.coverage_details[req_id]

        status_class = "badge-success" if cov.is_implemented else ("badge-warning" if cov.total_percentage > 0 else "badge-error")
        status_text = "Implemented" if cov.is_implemented else ("Partial" if cov.total_percentage > 0 else "Missing")

        created_at = "Unknown"
        created_by = "N/A"
        if req.created:
            created_at = _format_date(req.created.timestamp)
            created_by = req.created.author

        last_at = "Unknown"
        last_by = "N/A"
        if req.last_changed:
            last_at = _format_date(req.last_changed.timestamp)
            last_by = req.last_changed.author

        # Calculate first implemented from traces
        first_impl_at = "Unknown"
        first_impl_by = "N/A"
        if cov.matches:
            # Sort by timestamp to find earliest
            matches_with_dates = [m for m in cov.matches if m.first_implemented]
            if matches_with_dates:
                # Find min while keeping mypy happy with narrowing
                earliest = min(matches_with_dates, key=lambda x: x.first_implemented.timestamp if x.first_implemented else 0)
                if earliest.first_implemented:
                    first_impl_at = _format_date(earliest.first_implemented.timestamp)
                    first_impl_by = earliest.first_implemented.author

        html += f"""
        <div class="req-card">
            <div class="req-header">
                <div class="req-title-group">
                    <span class="req-id">{req.id}</span>
                    <span class="req-title">{req.title}</span>
                </div>
                <span class="badge {status_class}">{status_text}</span>
            </div>

            <p style="color: var(--text-secondary); margin: 0;">{req.description}</p>

            <div class="progress-container">
                <div class="progress-header">
                    <span>Implementation Coverage</span>
                    <span>{cov.total_percentage}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(100, cov.total_percentage)}%"></div>
                </div>
            </div>

            <div class="history-section">
                <div class="history-title">History & Metadata</div>
                <div class="history-grid">
                    <div class="history-item">
                        <span class="history-label">Requirement Written</span>
                        <span class="history-value">{created_at}</span> by <i>{created_by}</i>
                    </div>
                    <div class="history-item">
                        <span class="history-label">First Implemented</span>
                        <span class="history-value">{first_impl_at}</span> by <i>{first_impl_by}</i>
                    </div>
                    <div class="history-item">
                        <span class="history-label">Requirement Last Modified</span>
                        <span class="history-value">{last_at}</span> by <i>{last_by}</i>
                    </div>
                </div>
            </div>

            <div class="traces-container">
                <div class="history-title" style="margin-bottom: 0.5rem">Trace Tags Found</div>
    """

        if not cov.matches:
            html += '<div class="empty-msg">No implementation traces found for this requirement.</div>'
        else:
            for match in cov.matches:
                match_last = _format_date(match.last_changed.timestamp if match.last_changed else None)
                match_author = match.last_changed.author if match.last_changed else "Unknown"
                html += f"""
                <div class="trace-item">
                    <div class="trace-info">
                        <span class="trace-file">{match.file_path}:L{match.line_number}</span>
                        <span class="trace-meta">Line last changed: {match_last}</span>
                    </div>
                    <span class="badge" style="background: rgba(255,255,255,0.05); color: var(--text-secondary); font-size: 0.6rem">
                        {match_author}
                    </span>
                </div>
                """

        html += """
            </div>
        </div>
        """

    html += """
    </div>
</body>
</html>
    """
    return html
