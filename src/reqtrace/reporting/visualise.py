"""
Multi-page HTML visualization generator for reqtrace reports.
"""
import datetime
import logging
from pathlib import Path
from typing import Optional

from ..analysis.coverage import CoverageReport
from ..git import get_line_first_commit, get_line_metadata, get_range_commits
from ..models import RequirementIndex
from .source_tree import build_source_tree, render_source_tree_node, rollup_source_tree

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

.toggle-btn {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.8rem;
    padding: 0 4px;
    margin-right: 4px;
    transition: transform 0.2s;
    outline: none;
}
.toggle-btn:hover {
    color: var(--accent-blue);
}
.toggle-btn.collapsed {
    transform: rotate(-90deg);
}
.hidden-row {
    display: none !important;
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
            history = get_range_commits(path, match.line_start, match.line_end)
            if history:
                match.history = history
                match.last_changed = max(history, key=lambda h: h.timestamp)
                match.first_implemented = min(history, key=lambda h: h.timestamp)

    for match in report.unmatched_traces:
        path = Path(match.file_path)
        history = get_range_commits(path, match.line_start, match.line_end)
        if history:
            match.history = history
            match.last_changed = max(history, key=lambda h: h.timestamp)
            match.first_implemented = min(history, key=lambda h: h.timestamp)


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
        (self.output_dir / "source").mkdir(exist_ok=True)
        (self.output_dir / "assets").mkdir(exist_ok=True)

        # Write assets
        (self.output_dir / "assets" / "style.css").write_text(COMMON_CSS)

        # Generate pages
        self._write_index()
        self._write_requirements_list()
        self._write_requirement_details()
        self._write_source_list()

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
                <a href="{base}source/index.html">Source Code</a>
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
        if self.report.source_stats:
            stats = self.report.source_stats
            percent = int((stats.mapped_lines / stats.total_lines) * 100) if stats.total_lines > 0 else 0
            content += f"""
        <div class="card">
            <h2 style="margin-top:0">Source Code Traceability</h2>
            <div style="display:flex; justify-content:space-between; margin-bottom:1rem; font-size:0.9rem">
                <div>
                    <div style="color:var(--text-secondary)">Total Files</div>
                    <div style="font-weight:600; font-size:1.1rem">{stats.total_files}</div>
                </div>
                <div>
                    <div style="color:var(--text-secondary)">Total Lines</div>
                    <div style="font-weight:600; font-size:1.1rem">{stats.total_lines}</div>
                </div>
                <div>
                    <div style="color:var(--text-secondary)">Mapped Lines</div>
                    <div style="font-weight:600; font-size:1.1rem; color:var(--accent-green)">{stats.mapped_lines}</div>
                </div>
                <div>
                    <div style="color:var(--text-secondary)">Unmapped Lines</div>
                    <div style="font-weight:600; font-size:1.1rem; color:var(--accent-red)">{stats.unmapped_lines}</div>
                </div>
            </div>
            """

            if stats.disabled_files > 0:
                content += f"""
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 1rem;">
                <span class="badge" style="background: rgba(255,255,255,0.1); color: var(--text-secondary); border: 1px solid rgba(255,255,255,0.2)">{stats.disabled_files} Disabled Files</span>
            </div>
            """

            content += f"""
            <p>Proportion of codebase mapped to requirements: <b>{percent}%</b></p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {percent}%; background-color: {_get_progress_color(percent)}"></div>
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

    def _render_requirement_node(self, req_id: str, depth: int, parent_id: str, children_map: dict) -> str:
        req = self.index.requirements[req_id]
        cov = self.report.coverage_details[req_id]
        status_class = "badge-success" if cov.is_implemented else ("badge-warning" if cov.total_percentage > 0 else "badge-error")
        status_text = "Implemented" if cov.is_implemented else ("Partial" if cov.total_percentage > 0 else "Missing")

        if len(children_map[req_id]) > 0:
            toggle_btn = f'<button class="toggle-btn collapsed" id="btn-{req_id}" onclick="toggleRow(\'{req_id}\')">▼</button>'
        else:
            toggle_btn = f"<span style=\"color:var(--text-secondary); margin-right:4px; font-family:'JetBrains Mono', monospace; display:inline-block; width:1.2rem; text-align:center\">{'└─ ' if depth > 0 else ''}</span>"

        row_html = f"""
        <tr id="row-{req_id}"{' class="hidden-row"' if depth > 0 else ""} {f'data-parent="{parent_id}"' if parent_id else ""}>
            <td style="padding-left: {0.75 + (depth * 2)}rem; white-space: nowrap;">
                {toggle_btn}
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
            child_rows += self._render_requirement_node(child_id, depth + 1, req_id, children_map)

        return row_html + child_rows

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
        for root_id in roots:
            rows += self._render_requirement_node(root_id, 0, "", children_map)

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
        <script>
        function toggleRow(reqId) {{
            const btn = document.getElementById('btn-' + reqId);
            if (!btn) return;
            btn.classList.toggle('collapsed');

            const tableRows = document.querySelectorAll('tr[data-parent]');
            tableRows.forEach(row => {{
                let parent = row.getAttribute('data-parent');
                let shouldHide = false;

                while (parent) {{
                    const parentBtn = document.getElementById('btn-' + parent);
                    if (parentBtn && parentBtn.classList.contains('collapsed')) {{
                        shouldHide = true;
                        break;
                    }}
                    const parentRow = document.getElementById('row-' + parent);
                    parent = parentRow ? parentRow.getAttribute('data-parent') : null;
                }}

                if (shouldHide) {{
                    row.classList.add('hidden-row');
                }} else {{
                    row.classList.remove('hidden-row');
                }}
            }});
        }}
        </script>
        """
        html = self._get_layout("Requirements", content, depth=1)
        (self.output_dir / "requirements" / "index.html").write_text(html)

    def _write_requirement_details(self):
        """Writes detail page for each requirement."""
        # Pre-compute children for all requirements
        children_map = {req_id: [] for req_id in self.index.requirements}
        for req in self.index.requirements.values():
            for parent_id in req.derived_from:
                if parent_id in children_map:
                    children_map[parent_id].append(req.id)

        # Pre-compute descendant traces
        descendant_traces_map = {}
        for rid in self.index.requirements:
            traces = []
            stack = [rid]
            while stack:
                current_id = stack.pop()
                for child_id in children_map.get(current_id, []):
                    child_cov = self.report.coverage_details[child_id]
                    for match in child_cov.matches:
                        traces.append((child_id, match))
                    stack.append(child_id)
            traces.sort(key=lambda x: (x[1].file_path, x[1].line_start))
            descendant_traces_map[rid] = traces

        for rid, req in self.index.requirements.items():
            cov = self.report.coverage_details[rid]

            content = f"""
            <a href="index.html" class="link" style="font-size:0.9rem">← Back to List</a>
            <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1.5rem">
                <h1 style="text-align:left">{rid}</h1>
                <span class="badge {'badge-success' if cov.is_implemented else 'badge-warning'}">{cov.total_percentage}%</span>
            </div>
            <h2 style="color:var(--text-primary); margin-top:0.25rem">{req.title}</h2>
            <p style="color:var(--text-secondary)">{req.description}</p>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin-top:2rem">
                {self._build_history_card(req)}
                {self._build_hierarchy_card(rid, req, children_map)}
            </div>

            {self._build_direct_traces_card(cov)}
            {self._build_derived_traces_card(rid, children_map, descendant_traces_map)}

            <div class="card" style="margin-top:2rem">
                <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Timeline</h3>
                {self._build_individual_timeline(req, cov)}
            </div>
            """
            html = self._get_layout(f"Detail {rid}", content, depth=1)
            (self.output_dir / "requirements" / f"{rid}.html").write_text(html)

    def _build_history_card(self, req) -> str:
        created_at = _format_date(req.created.timestamp if req.created else None)
        last_changed = _format_date(req.last_changed.timestamp if req.last_changed else None)
        return f"""
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
        """

    def _build_hierarchy_card(self, rid: str, req, children_map: dict) -> str:
        parents_html = " , ".join([f'<a href="{d}.html" class="link">{d}</a>' for d in req.derived_from]) or "None"
        children_html = " , ".join([f'<a href="{c}.html" class="link">{c}</a>' for c in sorted(children_map[rid])]) or "None"
        return f"""
        <div class="card">
            <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Hierarchy</h3>
            <div style="font-size:0.9rem">
                <div style="margin-bottom:1rem">
                    <div style="color:var(--text-secondary); font-size:0.75rem">Derived From (Parents)</div>
                    <div>{parents_html}</div>
                </div>
                <div>
                    <div style="color:var(--text-secondary); font-size:0.75rem">Derived By (Children)</div>
                    <div>{children_html}</div>
                </div>
            </div>
        </div>
        """

    def _build_direct_traces_card(self, cov) -> str:
        traces = ""
        for m in cov.matches:
            m_date = _format_date(m.last_changed.timestamp if m.last_changed else None)
            traces += f"""
            <div style="padding: 0.75rem; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <code style="color:var(--accent-blue)">{m.file_path}:L{m.line_start}-L{m.line_end}</code>
                    <div style="font-size:0.75rem; color:var(--text-secondary)">Last changed: {m_date}</div>
                </div>
                <span class="badge" style="background:rgba(255,255,255,0.05)">{m.last_changed.author if m.last_changed else "Unknown"}</span>
            </div>
            """
        if not traces:
            traces = (
                "<div style='padding:2rem; text-align:center; color:var(--text-secondary)'>No direct implementation traces found.</div>"
            )

        return f"""
        <div class="card" style="margin-top:2rem">
            <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Direct Implementation Traces</h3>
            {traces}
        </div>
        """

    def _build_derived_traces_card(self, rid: str, children_map: dict, descendant_traces_map: dict) -> str:
        if len(children_map.get(rid, [])) == 0:
            return ""

        child_traces_html = ""
        for child_id, m in descendant_traces_map[rid]:
            m_date = _format_date(m.last_changed.timestamp if m.last_changed else None)
            child_traces_html += f"""
            <div style="padding: 0.75rem; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <code style="color:var(--accent-blue)">{m.file_path}:L{m.line_start}-L{m.line_end}</code>
                    <span style="margin-left:8px; font-size:0.75rem; color:var(--text-secondary)">via <a href="{child_id}.html" class="link">{child_id}</a></span>
                    <div style="font-size:0.75rem; color:var(--text-secondary)">Last changed: {m_date}</div>
                </div>
                <span class="badge" style="background:rgba(255,255,255,0.05)">{m.last_changed.author if m.last_changed else "Unknown"}</span>
            </div>
            """
        if not child_traces_html:
            child_traces_html = (
                "<div style='padding:2rem; text-align:center; color:var(--text-secondary)'>No derived implementation traces found.</div>"
            )

        return f"""
        <div class="card" style="margin-top:2rem">
            <h3 style="margin-top:0; font-size:0.9rem; text-transform:uppercase; color:var(--text-secondary)">Derived Implementation Traces</h3>
            {child_traces_html}
        </div>
        """

    def _build_individual_timeline(self, req, cov) -> str:
        # pylint: disable=too-many-locals, too-many-branches
        events = []
        if req.created:
            events.append(
                {
                    "time": req.created.timestamp,
                    "label": "Requirement Created",
                    "author": req.created.author,
                    "commit_hash": req.created.commit_hash,
                    "commit_subject": req.created.commit_subject,
                }
            )
        if req.last_changed and req.created and req.last_changed.timestamp > req.created.timestamp:
            events.append(
                {
                    "time": req.last_changed.timestamp,
                    "label": "Requirement Modified",
                    "author": req.last_changed.author,
                    "commit_hash": req.last_changed.commit_hash,
                    "commit_subject": req.last_changed.commit_subject,
                }
            )

        all_commits = []
        for m in cov.matches:
            all_commits.extend(m.history)

        unique_commits = {}
        for c in all_commits:
            if c.commit_hash and c.commit_hash not in unique_commits:
                unique_commits[c.commit_hash] = c

        sorted_commits = sorted(unique_commits.values(), key=lambda x: x.timestamp)

        if sorted_commits:
            first_commit = sorted_commits[0]
            events.append(
                {
                    "time": first_commit.timestamp,
                    "label": "Implementation Started",
                    "author": first_commit.author,
                    "commit_hash": first_commit.commit_hash,
                    "commit_subject": first_commit.commit_subject,
                }
            )

            subsequent_commits = sorted_commits[1:]
            if subsequent_commits:
                latest_commit = subsequent_commits[-1]
                author_label = "Multiple" if len(set(c.author for c in subsequent_commits)) > 1 else latest_commit.author
                events.append(
                    {
                        "time": latest_commit.timestamp,
                        "label": f"Implementation Modified ({len(subsequent_commits)} changes)",
                        "author": author_label,
                        "is_collapse": True,
                        "commits": sorted(subsequent_commits, key=lambda x: x.timestamp, reverse=True),
                    }
                )

        events.sort(key=lambda x: x["time"], reverse=True)

        timeline_items = ""
        for e in events:
            if e.get("is_collapse"):
                commit_html = f"""
                <details style="margin-top:0.5rem; background:rgba(0,0,0,0.2); border-radius:0.5rem; padding:0.5rem;">
                    <summary style="cursor:pointer; color:var(--accent-yellow); font-size:0.8rem; font-weight:600;">View {len(e['commits'])} Commits</summary>
                    <div style="margin-top:0.5rem; display:flex; flex-direction:column; gap:0.5rem;">
                """
                for c in e["commits"]:
                    short_hash = c.commit_hash[:7] if c.commit_hash else ""
                    commit_html += f"""
                        <div style="font-family:'JetBrains Mono', monospace; font-size:0.75rem; color:var(--text-secondary); border-left:2px solid rgba(255,255,255,0.1); padding-left:0.5rem;">
                            <span style="color:var(--accent-yellow)">{short_hash}</span> {c.commit_subject} <span style="opacity:0.6">- {c.author}</span>
                        </div>
                    """
                commit_html += """
                    </div>
                </details>
                """
            else:
                commit_html = ""
                if e.get("commit_hash"):
                    short_hash = e["commit_hash"][:7]
                    subject = e.get("commit_subject", "")
                    commit_html = f"""
                    <div style="margin-top:0.5rem; background:rgba(0,0,0,0.2); padding:0.5rem; border-radius:0.5rem; font-family:'JetBrains Mono', monospace; font-size:0.75rem; color:var(--text-secondary)">
                        <span style="color:var(--accent-yellow)">{short_hash}</span> {subject}
                    </div>
                    """

            timeline_items += f"""
            <div style="padding: 1.5rem; border-left: 2px solid var(--accent-blue); margin-left: 1rem; position: relative;">
                <div style="position: absolute; width: 12px; height: 12px; background: var(--accent-blue); border-radius: 50%; left: -7px; top: 1.8rem"></div>
                <div style="color:var(--text-secondary); font-size:0.75rem">{_format_date(e['time'])}</div>
                <div style="font-weight:800; color:var(--accent-blue)">{e['label']}</div>
                <div style="font-size:0.85rem; color:var(--text-secondary)">By {e['author']}</div>
                {commit_html}
            </div>
            """
        if not timeline_items:
            return "<div style='padding:2rem; text-align:center; color:var(--text-secondary)'>No timeline events found.</div>"
        return timeline_items

    def _write_source_list(self):
        """Writes the list of all source files and their coverage as an expandable tree."""
        if not self.report.source_stats:
            html = self._get_layout(
                "Source Code",
                "<div style='padding:2rem; text-align:center; color:var(--text-secondary)'>No source code stats available.</div>",
                depth=1,
            )
            (self.output_dir / "source" / "index.html").write_text(html)
            return

        root = build_source_tree(self.report.source_stats.file_stats)
        rollup_source_tree(root)

        node_counter = [0]
        rows = render_source_tree_node(root, -1, None, node_counter, _get_progress_color)

        content = f"""
        <h1>Source Code Traceability</h1>
        <p class="subtitle">Detailed breakdown of requirement coverage mapped to source files.</p>
        <div class="card" style="margin-top: 2rem">
            <table>
                <thead>
                    <tr>
                        <th style="width: 40%">File Path</th>
                        <th style="width: 15%">Lines (Mapped/Total)</th>
                        <th style="width: 10%">Coverage</th>
                        <th style="width: 35%">Progress</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        <script>
        function toggleDetails(nodeId, btn) {{
            const row = document.getElementById('details-' + nodeId);
            if (row) {{
                row.classList.toggle('hidden-row');
                btn.classList.toggle('collapsed');
            }}
        }}

        function toggleFolder(nodeId, btn) {{
            const isCollapsing = !btn.classList.contains('collapsed');
            btn.classList.toggle('collapsed');
            btn.innerText = isCollapsing ? '▶' : '▼';

            // We need to recursively hide/show all children
            const toggleChildren = (parentId, hide) => {{
                const trs = document.querySelectorAll(`tr[data-parent="${{parentId}}"]`);
                trs.forEach(tr => {{
                    // Check if this row is a details row and shouldn't be shown
                    if (tr.classList.contains('tree-details')) {{
                        // Unmapped details should only be shown if its parent file is NOT collapsed
                        // But wait! Files themselves can't be collapsed in our model, only folders.
                        // Actually, our unmapped toggle handles details. If folder hides, details ALWAYS hide.
                        // If folder shows, details ONLY show if the file toggle isn't collapsed.
                        const fileNodeId = tr.id.split('-')[1];
                        const fileToggle = document.querySelector(`#node-${{fileNodeId}} .toggle-btn`);
                        if (hide || (fileToggle && fileToggle.classList.contains('collapsed'))) {{
                            tr.classList.add('hidden-row');
                        }} else {{
                            tr.classList.remove('hidden-row');
                        }}
                    }} else {{
                        if (hide) {{
                            tr.classList.add('hidden-row');
                        }} else {{
                            tr.classList.remove('hidden-row');
                        }}
                    }}

                    // If this child is a folder itself, recurse
                    const childNodeIdStr = tr.id.replace('node-', '').replace('details-', '');
                    const childNodeId = parseInt(childNodeIdStr);

                    if (!isNaN(childNodeId) && !tr.classList.contains('tree-details')) {{
                        const childToggle = tr.querySelector('.toggle-btn');
                        if (childToggle && !childToggle.classList.contains('collapsed')) {{
                             // This is an open sub-folder. We must process its kids too!
                             // If we are hiding everything, we hide its kids unconditionally.
                             // If we are showing, we show its kids because it's open.
                             toggleChildren(childNodeId, hide);
                        }} else if (childToggle && childToggle.classList.contains('collapsed')) {{
                             // This is a closed sub-folder.
                             // If hiding everything, recurse hide to ensure nothing slips through
                             if (hide) {{
                                 toggleChildren(childNodeId, hide);
                             }}
                             // If showing, do NOT recurse, leave it closed.
                        }}
                    }}
                }});
            }};

            toggleChildren(nodeId, isCollapsing);
        }}
        </script>
        """
        html = self._get_layout("Source Code", content, depth=1)
        (self.output_dir / "source" / "index.html").write_text(html)


def generate_html(index: RequirementIndex, report: CoverageReport, output_dir: Path):
    """Entry point for generating the multi-page report."""
    generator = MultiPageGenerator(index, report, output_dir)
    generator.generate()
