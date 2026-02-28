"""
Command line interface for reqtrace.
"""
import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .scanner import scan_directory, scan_file
from .coverage import calculate_coverage
from .parser import load_yaml, parse_requirements


def main(args: Optional[List[str]] = None):
    """CLI Entrypoint for reqtrace."""
    # pylint: disable=too-many-locals
    # @trace: REQ-CLI
    parser = argparse.ArgumentParser(description="Reqtrace: A GitOps-friendly requirements tracer.")

    parser.add_argument("--reqs", nargs="+", required=True, help="Path(s) to YAML requirement files.")

    parser.add_argument(
        "--src",
        nargs="+",
        required=True,
        help="Path(s) to source code directories or files to scan.",
    )

    parsed_args = parser.parse_args(args)

    try:
        # 1. Load the requirements
        print(f"Loading requirements from {parsed_args.reqs}...")
        all_req_data = []
        for req_path in parsed_args.reqs:
            all_req_data.extend(load_yaml(req_path))

        req_index = parse_requirements(all_req_data)

        # 2. Scan the source code
        print(f"Scanning source code at {parsed_args.src}...")
        all_traces = []
        for src_path in parsed_args.src:
            path = Path(src_path)
            if path.is_file():
                all_traces.extend(scan_file(path))
            elif path.is_dir():
                all_traces.extend(scan_directory(path))
            else:
                print(
                    f"Warning: Source path {src_path} is neither file nor directory.",
                    file=sys.stderr,
                )

        # 3. Calculate Coverage
        sys.stdout.write("Calculating traceability matrix...\n\n")
        report = calculate_coverage(req_index, all_traces)

        # 4. Print Report
        print("=== REQTRACE COVERAGE REPORT ===")
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
                print(f"Unknown ID: '{trace.req_id}' {pct_str} at {trace.file_path}:{trace.line_number}")

        # Exit with error code if coverage is not 100%
        # (This fails the CI pipeline intentionally if requirements aren't met!)
        if report.missing_requirements > 0 or report.partial_requirements > 0:
            sys.exit(1)

        sys.exit(0)

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error running reqtrace: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
