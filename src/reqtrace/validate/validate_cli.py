"""
CLI for validating .rqtr requirement files against the reqtrace schema.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import List, Optional

import yaml
import jsonschema

from .schema import RQTR_SCHEMA

log = logging.getLogger(__name__)


def validate_file(path: Path) -> List[str]:
    """
    Load and validate a single .rqtr file against RQTR_SCHEMA.

    Returns a list of error messages (empty list means the file is valid).
    """
    errors: List[str] = []

    # @trace-start: REQ-VALIDATE-SCHEMA
    # 1. Check the file exists and is readable YAML
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        errors.append(f"File not found: {path}")
        return errors
    except yaml.YAMLError as exc:
        errors.append(f"YAML parse error in '{path}': {exc}")
        return errors

    # 2. Validate against JSON Schema
    validator = jsonschema.Draft7Validator(RQTR_SCHEMA)
    for error in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        location = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        errors.append(f"  [{location}] {error.message}")

    return errors
    # @trace-end: REQ-VALIDATE-SCHEMA


def main(args: Optional[List[str]] = None) -> None:
    """CLI entrypoint for reqtrace-validate."""
    parser = argparse.ArgumentParser(
        prog="reqtrace-validate",
        description="Validate .rqtr requirement files against the reqtrace schema.",
    )
    parser.add_argument(
        "files",
        metavar="FILE",
        nargs="+",
        help="One or more .rqtr files to validate.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging output.",
    )

    parsed = parser.parse_args(args)

    logging.basicConfig(
        level=logging.DEBUG if parsed.verbose else logging.INFO,
        format="%(message)s",
    )

    all_valid = True
    # @trace-start: SYS-VALIDATE

    for file_str in parsed.files:
        path = Path(file_str)
        errors = validate_file(path)
        if errors:
            all_valid = False
            print(f"❌ INVALID: {path}")
            for err in errors:
                print(err)
        else:
            print(f"✅ VALID:   {path}")

    # @trace-end: SYS-VALIDATE
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
