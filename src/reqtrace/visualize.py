"""
Multi-page HTML visualization generator for reqtrace reports.
"""
import datetime
import logging
from pathlib import Path
from typing import Optional
from .models import RequirementIndex
from .coverage import CoverageReport
from .git import get_line_metadata, get_line_first_commit

log = logging.getLogger(__name__)

# Common CSS for all pages
COMMON_CSS = """
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
    --nav-bg: rgba(15, 23, 42, 0.8);
}

body {
    background-color: var(--bg-color);
    color: var(--text-primary);
    font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
    margin: 0;
    padding: 0;
    line-height: 1.6;
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 2rem;
}

nav {
    background: var(--nav-bg);
    backdrop-filter: blur(10px);
    border-bottom: 1px solid var(--glass-border);
    position: sticky;
    top: 0;
    z-index: 100;
    padding: 0.75rem 0;
}

.nav-content {
    max-width: 1100px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 2rem;
}

.nav-logo {
    font-weight: 800;
    font-size: 1.25rem;
    color: var(--accent-blue);
    text-decoration: none;
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-links a {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 0.9rem;
    font-weight: 600;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: var(--accent-blue);
}

header {
    margin-bottom: 3rem;
    text-align: center;
    padding-top: 2rem;
}

h1 {
    font-size: 2.5rem;
    letter-spacing: -0.02em;
    color: var(--accent-blue);
    margin: 0;
    font-weight: 800;
}

.subtitle {
    color: var(--text-secondary);
    margin-top: 0.5rem;
    font-size: 1rem;
}

.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.stat-card {
    background: var(--card-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    padding: 1.5rem;
    border-radius: 1rem;
    text-align: center;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);
}

.stat-value {
    font-size: 2rem;
    font-weight: 800;
    display: block;
    margin-bottom: 0.25rem;
}

.stat-label {
    color: var(--text-secondary);
    font-size: 0.7rem;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.1em;
}

.card {
    background: var(--card-bg);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 1rem;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.badge {
    padding: 0.3rem 0.8rem;
    border-radius: 0.5rem;
    font-size: 0.7rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    display: inline-block;
}

.badge-success { background: rgba(74, 222, 128, 0.15); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.2); }
.badge-warning { background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid rgba(251, 191, 36, 0.2); }
.badge-error { background: rgba(248, 113, 113, 0.15); color: #f87171; border: 1px solid rgba(248, 113, 113, 0.2); }

.progress-bar {
    width: 100%;
    height: 8px;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 8px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--accent-blue);
}

table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

th {
    text-align: left;
    color: var(--text-secondary);
    font-size: 0.75rem;
    text-transform: uppercase;
    padding: 0.75rem;
    border-bottom: 1px solid var(--glass-border);
}

td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--glass-border);
}

tr:last-child td {
    border-bottom: none;
}

.link {
    color: var(--accent-blue);
    text-decoration: none;
    font-weight: 600;
}

.link:hover {
    text-decoration: underline;
}

pre {
    background: rgba(0,0,0,0.3);
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
}
"""


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


def _get_progress_color(percentage: float) -> str:
    """Returns a CSS color transitioning from red (0%) to yellow (50%) to green (100%)."""
    if percentage < 0:
        percentage = 0
    elif percentage > 100:
        percentage = 100
    hue = int((percentage / 100.0) * 120)
    return f"hsl({hue}, 80%, 45%)"


class MultiPageGenerator:
    """Generates a multi-page HTML report."""

    # pylint: disable=too-few-public-methods

    def __init__(self, index: RequirementIndex, report: CoverageReport, output_dir: Path):
        self.index = index
        self.report = report
        self.output_dir = output_dir
        self.base_url = "."  # Default relative path from current page to root

    def generate(self):
        """Generates the entire report structure."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "requirements").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)

        # Write assets
        (self.output_dir / "assets" / "style.css").write_text(COMMON_CSS)

        # Generate pages
        self._write_index()
        self._write_requirements_list()
        self._write_requirement_details()
        self._write_timeline()

    def _get_layout(self, title: str, content: str, depth: int = 0) -> str:
        """Shared HTML layout with navigation."""
        base = "../" * depth if depth > 0 else "./"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Reqtrace</title>
    <link rel="stylesheet" href="{base}assets/style.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&family=JetBrains+Mono&display=swap" rel="stylesheet">
</head>
<body>
    <nav>
        <div class="nav-content">
            <a href="{base}index.html" class="nav-logo">Reqtrace</a>
            <div class="nav-links">
                <a href="{base}index.html">Dashboard</a>
                <a href="{base}requirements/index.html">Requirements</a>
                <a href="{base}timeline.html">Timeline</a>
            </div>
        </div>
    </nav>
    <div class="container">
        {content}
    </div>
</body>
</html>
"""

    def _write_index(self):
        """Writes the dashboard index page."""
        content = f"""
        <header>
            <h1>Report Dashboard</h1>
            <div class="subtitle">Traceability Matrix Governance Overview</div>
            <div style="font-size: 0.85rem; margin-top: 1rem; color: var(--text-secondary)">
                Generated: {_format_date(int(datetime.datetime.now().timestamp()))}
            </div>
        </header>

        <div class="summary-grid">
            <div class="stat-card" style="border-top: 3px solid var(--accent-blue)">
                <span class="stat-value">{self.report.total_requirements}</span>
                <span class="stat-label">Requirements</span>
            </div>
            <div class="stat-card" style="border-top: 3px solid var(--accent-green)">
                <span class="stat-value" style="color: var(--accent-green)">{self.report.implemented_requirements}</span>
                <span class="stat-label">Full Coverage</span>
            </div>
            <div class="stat-card" style="border-top: 3px solid var(--accent-yellow)">
                <span class="stat-value" style="color: var(--accent-yellow)">{self.report.partial_requirements}</span>
                <span class="stat-label">Partial Coverage</span>
            </div>
            <div class="stat-card" style="border-top: 3px solid var(--accent-red)">
                <span class="stat-value" style="color: var(--accent-red)">{self.report.missing_requirements}</span>
                <span class="stat-label">Missing</span>
            </div>
        </div>

        <div class="card">
            <h2 style="margin-top:0">Project Summary</h2>
            <p>Overall implementation progress: <b>{self._calculate_global_percent()}%</b></p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {self._calculate_global_percent()}%; background-color: {_get_progress_color(self._calculate_global_percent())}"></div>
            </div>
        </div>
        """
        html = self._get_layout("Dashboard", content)
        (self.output_dir / "index.html").write_text(html)

    def _calculate_global_percent(self) -> int:
        if not self.report.total_requirements:
            return 0
        total = sum(c.total_percentage for c in self.report.coverage_details.values())
        return int(total / self.report.total_requirements)

    def _write_requirements_list(self):
        """Writes the list of all requirements as a tree."""
        # 1. Build parent->children mapping and identify roots
        children_map = {req_id: [] for req_id in self.index.requirements}
        has_parent = set()
        for req in self.index.requirements.values():
            for parent_id in req.derived_from:
                if parent_id in children_map:
                    children_map[parent_id].append(req.id)
                    has_parent.add(req.id)

        roots = sorted([r for r in self.index.requirements if r not in has_parent])

        rows = ""

        def render_node(req_id: str, depth: int) -> str:
            req = self.index.requirements[req_id]
            cov = self.report.coverage_details[req_id]
            status_class = "badge-success" if cov.is_implemented else ("badge-warning" if cov.total_percentage > 0 else "badge-error")
            status_text = "Implemented" if cov.is_implemented else ("Partial" if cov.total_percentage > 0 else "Missing")

            padding_left = 0.75 + (depth * 2)  # Base padding + 2rem per depth level
            prefix = "└─ " if depth > 0 else ""

            row_html = f"""
            <tr>
                <td style="padding-left: {padding_left}rem">
                    <span style="color:var(--text-secondary); margin-right:4px; font-family:'JetBrains Mono', monospace">{prefix}</span>
                    <a href="{req_id}.html" class="link">{req_id}</a>
                </td>
                <td>{req.title}</td>
                <td><span class="badge {status_class}">{status_text}</span></td>
                <td>
                    <div class="progress-bar" style="height:4px">
                        <div class="progress-fill" style="width: {cov.total_percentage}%; background-color: {_get_progress_color(cov.total_percentage)}"></div>
                    </div>
                    <span style="font-size:0.75rem">{cov.total_percentage}%</span>
                </td>
            </tr>
            """

            child_rows = ""
            for child_id in sorted(children_map[req_id]):
                child_rows += render_node(child_id, depth + 1)

            return row_html + child_rows

        for root_id in roots:
            rows += render_node(root_id, 0)

        content = f"""
        <h1>Requirements List</h1>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Title</th>
                        <th>Status</th>
                        <th>Coverage</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """
        html = self._get_layout("Requirements", content, depth=1)
        (self.output_dir / "requirements" / "index.html").write_text(html)

    def _write_requirement_details(self):
        """Writes detail page for each requirement."""
        for rid, req in self.index.requirements.items():
            cov = self.report.coverage_details[rid]

            # History items
            created_at = _format_date(req.created.timestamp if req.created else None)
            last_changed = _format_date(req.last_changed.timestamp if req.last_changed else None)

            traces = ""
            for m in cov.matches:
                m_date = _format_date(m.last_changed.timestamp if m.last_changed else None)
                traces += f"""
                <div style="padding: 0.75rem; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <code style="color:var(--accent-blue)">{m.file_path}:L{m.line_number}</code>
                        <div style="font-size:0.75rem; color:var(--text-secondary)">Last changed: {m_date}</div>
                    </div>
                    <span class="badge" style="background:rgba(255,255,255,0.05)">{m.last_changed.author if m.last_changed else "Unknown"}</span>
                </div>
                """

            if not traces:
                traces = "<div style='padding:2rem; text-align:center; color:var(--text-secondary)'>No implementation traces found.</div>"

            content = f"""
            <a href="index.html" class="link" style="font-size:0.9rem">← Back to List</a>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1.5rem">
                <h1 style="text-align:left">{rid}</h1>
                <span class="badge {'badge-success' if cov.is_implemented else 'badge-warning'}">{cov.total_percentage}%</span>
            </div>
            <h2 style="color:var(--text-primary); margin-top:0.25rem">{req.title}</h2>
            <p style="color:var(--text-secondary)">{req.description}</p>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top:2rem">
                <div class="card">
                    <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">History</h3>
                    <div style="font-size:0.9rem">
                        <div style="margin-bottom:1rem">
                            <div style="color:var(--text-secondary); font-size:0.75rem">First Defined</div>
                            <div>{created_at} by <b>{req.created.author if req.created else "N/A"}</b></div>
                        </div>
                        <div>
                            <div style="color:var(--text-secondary); font-size:0.75rem">Last Modified</div>
                            <div>{last_changed} by <b>{req.last_changed.author if req.last_changed else "N/A"}</b></div>
                        </div>
                    </div>
                </div>
                <div class="card">
                    <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Hierarchy</h3>
                    <div style="font-size:0.9rem">
                        <div style="color:var(--text-secondary); font-size:0.75rem">Derived From</div>
                        <div>{' , '.join([f'<a href="{d}.html" class="link">{d}</a>' for d in req.derived_from]) or "None"}</div>
                    </div>
                </div>
            </div>

            <div class="card" style="margin-top:2rem">
                <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Implementation Traces</h3>
                {traces}
            </div>
            """
            html = self._get_layout(f"Detail {rid}", content, depth=1)
            (self.output_dir / "requirements" / f"{rid}.html").write_text(html)

    def _write_timeline(self):
        """Writes a simple chronological timeline of requirement/trace events."""
        events = []
        for rid, req in self.index.requirements.items():
            if req.created:
                events.append({"time": req.created.timestamp, "label": "Requirement Created", "id": rid, "author": req.created.author})

            cov = self.report.coverage_details[rid]
            # First implementation timestamp
            impl_dates = [m.first_implemented.timestamp for m in cov.matches if m.first_implemented]
            if impl_dates:
                events.append(
                    {
                        "time": min(impl_dates),
                        "label": "Implementation Started",
                        "id": rid,
                        "author": "System",  # Or find specific author
                    }
                )

        events.sort(key=lambda x: x["time"], reverse=True)

        timeline_items = ""
        for e in events:
            timeline_items += f"""
            <div style="padding: 1.5rem; border-left: 2px solid var(--accent-blue); margin-left: 1rem; position: relative;">
                <div style="position: absolute; width: 12px; height: 12px; background: var(--accent-blue); border-radius: 50%; left: -7px; top: 1.8rem"></div>
                <div style="color:var(--text-secondary); font-size:0.75rem">{_format_date(e['time'])}</div>
                <div style="font-weight:800; color:var(--accent-blue)">{e['label']}</div>
                <div style="font-size:1.1rem; font-weight:600"><a href="requirements/{e['id']}.html" class="link">{e['id']}</a></div>
                <div style="font-size:0.85rem; color:var(--text-secondary)">By {e['author']}</div>
            </div>
            """

        content = f"""
        <h1>Project Timeline</h1>
        <div class="card">
            {timeline_items}
        </div>
        """
        html = self._get_layout("Timeline", content)
        (self.output_dir / "timeline.html").write_text(html)


def generate_html(index: RequirementIndex, report: CoverageReport, output_dir: Path):
    """Entry point for generating the multi-page report."""
    generator = MultiPageGenerator(index, report, output_dir)
    generator.generate()
