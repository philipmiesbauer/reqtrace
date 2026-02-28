"""
Command line interface for reqtrace.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .scanner import scan_directory, scan_file
from .coverage import calculate_coverage
from .models import TraceMatch
from .parser import load_yaml, parse_requirements
from .visualize import enrich_metadata, generate_html

log = logging.getLogger(__name__)


def _load_requirements(req_path_strs: List[str]) -> List[dict]:
    """Expand any directories into YAML files, then load all requirement data."""
    req_files: List[Path] = []
    for req_path_str in req_path_strs:
        reg_path = Path(req_path_str)
        if reg_path.is_dir():
            req_files.extend(sorted(reg_path.rglob("*.yml")))
        elif reg_path.is_file():
            req_files.append(reg_path)
        else:
            log.warning("Requirement path '%s' is neither a file nor a directory.", req_path_str)
    if not req_files:
        log.warning("No requirement files found.")
    # Make file paths unique
    req_files = list(set(req_files))
    all_req_data: List[dict] = []
    for req_file in req_files:
        all_req_data.extend(load_yaml(req_file))
    return all_req_data


def _load_source_code(src_path_strs: List[str]) -> List[TraceMatch]:
    """Scan source files/directories and return all found trace matches."""
    all_traces: List[TraceMatch] = []
    for src_path_str in src_path_strs:
        src_path = Path(src_path_str)
        if src_path.is_file():
            all_traces.extend(scan_file(src_path))
        elif src_path.is_dir():
            all_traces.extend(scan_directory(src_path))
        else:
            log.warning("Source path '%s' is neither a file nor a directory.", src_path_str)
    if not all_traces:
        log.warning("No source code traces found.")
    # Make file paths unique
    all_traces = list(set(all_traces))
    return all_traces


def main(args: Optional[List[str]] = None):
    """CLI Entrypoint for reqtrace."""
    # @trace-start: REQ-CLI
    parser = argparse.ArgumentParser(description="Reqtrace: A GitOps-friendly requirements tracer.")

    parser.add_argument(
        "--reqs", default=["reqs/"], nargs="+", help="Path(s) to YAML requirement files or folder containing them. (Default: reqs/)"
    )

    parser.add_argument(
        "--src",
        default=["src/"],
        nargs="+",
        help="Path(s) to source code directories or files to scan. (Default: src/)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )

    parser.add_argument(
        "--html",
        metavar="DIR",
        help="Generate a structured multi-page HTML report in the specified directory.",
    )

    parsed_args = parser.parse_args(args)

    logging.basicConfig(
        level=logging.DEBUG if parsed_args.verbose else logging.INFO,
        format="%(message)s",
    )

    try:
        # 1. Load the requirements
        log.info("Loading requirements from %s...", parsed_args.reqs)
        all_req_data = _load_requirements(parsed_args.reqs)
        req_index = parse_requirements(all_req_data)

        # 2. Scan the source code
        log.info("Scanning source code at %s...", parsed_args.src)
        all_traces = _load_source_code(parsed_args.src)

        # 3. Calculate Coverage
        log.info("Calculating traceability matrix...")
        report = calculate_coverage(req_index, all_traces)

        # 4. Generate HTML Report (if requested)
        if parsed_args.html:
            enrich_metadata(req_index, report)

            output_dir = Path(parsed_args.html)
            generate_html(req_index, report, output_dir)
            log.info("Multi-page HTML report generated at: %s", output_dir.absolute())

        # 5. Print Summary to Console (plain output)
        print("\n=== REQTRACE COVERAGE REPORT ===")
        print(f"Total Requirements: {report.total_requirements}")
        print(f"Implemented (>=100%):  {report.implemented_requirements}")
        print(f"Partial (<100%):  {report.partial_requirements}")
        print(f"Missing (0%):     {report.missing_requirements}\n")

        print("--- DETAILS ---")
        for req_id, cov in report.coverage_details.items():
            status = "✅ IMPLEMENTED" if cov.is_implemented else ("⚠️ PARTIAL" if cov.total_percentage > 0 else "❌ MISSING")
            print(f"[{status}] {req_id} - Coverage: {cov.total_percentage}%")

        if report.unmatched_traces:
            print("\n--- WARNING: UNMATCHED TRACE TAGS ---")
            print("The following trace tags refer to unknown requirement IDs.")
            for trace in report.unmatched_traces:
                pct_str = f"({trace.percentage}%)" if trace.percentage else ""
                print(f"Unknown ID: '{trace.req_id}' {pct_str} at {trace.file_path}:{trace.line_start}-{trace.line_end}")

        # Exit with error code if coverage is not 100%
        # (This fails the CI pipeline intentionally if requirements aren't met!)
        if report.missing_requirements > 0 or report.partial_requirements > 0:
            sys.exit(1)

        sys.exit(0)
        # @trace-end: REQ-CLI

    except Exception as e:  # pylint: disable=broad-exception-caught
        log.error("Error running reqtrace: %s", e)
        sys.exit(2)


if __name__ == "__main__":
    main()
