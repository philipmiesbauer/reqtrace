"""
CLI for reqtrace-exchange: import ReqIF → .rqtr and export .rqtr → ReqIF.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .reqif_importer import import_reqif
from .reqif_exporter import export_reqif

log = logging.getLogger(__name__)


def _add_verbose(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose (DEBUG) logging.")


def main(args: Optional[List[str]] = None) -> None:
    """CLI entrypoint for reqtrace-exchange."""
    parser = argparse.ArgumentParser(
        prog="reqtrace-exchange",
        description="Import and export reqtrace (.rqtr) files to/from ReqIF format.",
    )
    _add_verbose(parser)

    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # --- import sub-command ---
    import_parser = subparsers.add_parser(
        "import",
        help="Import a ReqIF file and write a .rqtr YAML file.",
    )
    import_parser.add_argument("input", metavar="INPUT.reqif", help="Path to the source .reqif file.")
    import_parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.rqtr",
        required=True,
        help="Path for the output .rqtr file.",
    )
    _add_verbose(import_parser)

    # --- export sub-command ---
    export_parser = subparsers.add_parser(
        "export",
        help="Export a .rqtr file as a ReqIF XML file.",
    )
    export_parser.add_argument("input", metavar="INPUT.rqtr", help="Path to the source .rqtr file.")
    export_parser.add_argument(
        "-o",
        "--output",
        metavar="OUTPUT.reqif",
        required=True,
        help="Path for the output .reqif file.",
    )
    _add_verbose(export_parser)

    parsed = parser.parse_args(args)

    logging.basicConfig(
        level=logging.DEBUG if parsed.verbose else logging.INFO,
        format="%(message)s",
    )

    try:
        # @trace-start: SYS-EXCHANGE
        if parsed.command == "import":
            input_path = Path(parsed.input)
            output_path = Path(parsed.output)
            log.info("Importing '%s' → '%s' ...", input_path, output_path)
            import_reqif(input_path, output_path)
            log.info("✅ Import complete: %s", output_path)

        elif parsed.command == "export":
            input_path = Path(parsed.input)
            output_path = Path(parsed.output)
            log.info("Exporting '%s' → '%s' ...", input_path, output_path)
            export_reqif(input_path, output_path)
            log.info("✅ Export complete: %s", output_path)
        # @trace-end: SYS-EXCHANGE

    except Exception as exc:  # pylint: disable=broad-exception-caught
        log.error("Error during %s: %s", parsed.command, exc)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
