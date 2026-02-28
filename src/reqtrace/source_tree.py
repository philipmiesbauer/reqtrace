"""
Source code tree logic for the reqtrace HTML visualization report.
"""
from typing import Dict, List, Optional
from pathlib import Path
from dataclasses import dataclass, field
from .models import FileStats


@dataclass
class SourceNode:
    """A node representing a file or directory in the source tree."""

    name: str
    is_dir: bool
    children: Dict[str, "SourceNode"] = field(default_factory=dict)
    fstat: Optional[FileStats] = None
    mapped_lines: int = 0
    total_lines: int = 0
    is_disabled: bool = False


def build_source_tree(file_stats: List[FileStats]) -> SourceNode:
    """Build a tree from the flat list of file stats."""
    root = SourceNode("root", True)

    for fstat in file_stats:
        parts = Path(fstat.file_path).parts
        current = root
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            if part not in current.children:
                current.children[part] = SourceNode(part, not is_last)
            current = current.children[part]
            if is_last:
                current.fstat = fstat
                if fstat.is_disabled:
                    current.is_disabled = True
                else:
                    current.mapped_lines = fstat.mapped_lines
                    current.total_lines = fstat.total_lines
    return root


def rollup_source_tree(node: SourceNode):
    """Roll up metrics from leaves to root."""
    if not node.is_dir:
        return

    dir_mapped = 0
    dir_total = 0
    all_disabled = True
    has_children = False

    for child in node.children.values():
        has_children = True
        rollup_source_tree(child)
        if not child.is_disabled:
            all_disabled = False
            dir_mapped += child.mapped_lines
            dir_total += child.total_lines

    node.mapped_lines = dir_mapped
    node.total_lines = dir_total
    if has_children and all_disabled:
        node.is_disabled = True


def _get_node_metrics_html(node: SourceNode, color_func) -> tuple[str, str, str, str, str]:
    if node.is_disabled:
        status_class = "badge"
        status_style = "background: rgba(255,255,255,0.1); color: var(--text-secondary); border: 1px solid rgba(255,255,255,0.2)"
        status_text = "DISABLED"
        progress_html = '<div class="progress-bar" style="height:4px; opacity:0.3"><div class="progress-fill" style="width: 0%; background-color: var(--text-secondary)"></div></div>'
        lines_text = "N/A"
    else:
        pct = int(node.mapped_lines / node.total_lines * 100) if node.total_lines > 0 else 0
        status_class = "badge-success" if pct == 100 else ("badge-warning" if pct > 0 else "badge-error")
        status_style = ""
        status_text = f"{pct}%"
        progress_html = f'<div class="progress-bar" style="height:4px"><div class="progress-fill" style="width: {pct}%; background-color: {color_func(pct)}"></div></div>'
        lines_text = f"{node.mapped_lines} / {node.total_lines}"

    return status_class, status_style, status_text, progress_html, lines_text


def _get_node_name_html(node: SourceNode, current_id: int) -> tuple[str, str, str]:
    unmapped_str = ""
    if node.is_dir:
        toggle_btn = f'<button class="toggle-btn" style="margin-right:4px;" onclick="toggleFolder({current_id}, this)">▼</button>'
        icon_color = "var(--text-secondary)" if node.is_disabled else "var(--brand-blue)"
        name_html = f'<span style="font-weight: 600; font-size: 0.95rem; color: {icon_color}">📁 {node.name}/</span>'
    else:
        if node.fstat and node.fstat.unmapped_ranges:
            unmapped_str = ", ".join(f"L{start}-L{end}" if start != end else f"L{start}" for start, end in node.fstat.unmapped_ranges)
            toggle_btn = (
                f'<button class="toggle-btn collapsed" style="margin-right:4px;" onclick="toggleDetails({current_id}, this)">▼</button>'
            )
        else:
            toggle_btn = '<span style="display:inline-block; width:1.2rem; margin-right:4px"></span>'

        file_color = "var(--text-secondary)" if node.is_disabled else "var(--text-primary)"
        name_html = (
            f"<span style=\"font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; color: {file_color}\">📄 {node.name}</span>"
        )
    return toggle_btn, name_html, unmapped_str


def _render_single_node(node: SourceNode, depth: int, current_id: int, parent_id: Optional[int], color_func) -> str:
    status_class, status_style, status_text, progress_html, lines_text = _get_node_metrics_html(node, color_func)
    toggle_btn, name_html, unmapped_str = _get_node_name_html(node, current_id)

    html_rows = f"""
    <tr id="node-{current_id}" class="tree-row {'child-row' if parent_id is not None else ''}" {f'data-parent="{parent_id}"' if parent_id is not None else ""}>
        <td style="white-space: nowrap; padding-left: {0.75 + (depth * 1.5)}rem;">
            {toggle_btn}
            {name_html}
        </td>
        <td style="{'; color:var(--text-secondary)' if node.is_disabled else ''}">{lines_text}</td>
        <td><span class="badge {status_class}" style="{status_style}">{status_text}</span></td>
        <td>
            {progress_html}
        </td>
    </tr>
    """

    if unmapped_str:
        html_rows += f"""
        <tr id="details-{current_id}" class="hidden-row tree-details" {f'data-parent="{parent_id}"' if parent_id is not None else ""}>
            <td colspan="4" style="padding: 1rem 1rem 1rem {0.75 + (depth * 1.5) + 1.5}rem; background: rgba(0,0,0,0.1)">
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem">Unmapped Lines:</div>
                <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--accent-red); line-height: 1.5">
                    {unmapped_str}
                </div>
            </td>
        </tr>
        """

    return html_rows


def render_source_tree_node(node: SourceNode, depth: int, parent_id: Optional[int], node_counter: List[int], color_func) -> str:
    """Recursively render HTML for a tree node and its children."""
    current_id = node_counter[0]
    node_counter[0] += 1

    html_rows = ""

    # Skip rendering the imaginary root node
    if depth >= 0:
        html_rows += _render_single_node(node, depth, current_id, parent_id, color_func)

    # Recursively render children
    # Sorted so directories are first, then files alphabetically
    sorted_kids = sorted(node.children.values(), key=lambda x: (not x.is_dir, x.name.lower()))
    for child in sorted_kids:
        next_depth = depth + 1 if depth >= 0 else 0
        next_parent = current_id if depth >= 0 else None
        html_rows += render_source_tree_node(child, next_depth, next_parent, node_counter, color_func)

    return html_rows
