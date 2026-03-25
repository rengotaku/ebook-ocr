"""Validate book.xml against XSD schema using lxml."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from lxml import etree

from src.logging_config import setup_logging

logger = logging.getLogger(__name__)

# XSD path relative to project root
DEFAULT_XSD_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "book.xsd"


def validate_xml(xml_path: Path, xsd_path: Path) -> list[str]:
    """Validate an XML file against an XSD schema.

    Args:
        xml_path: Path to the XML file.
        xsd_path: Path to the XSD schema file.

    Returns:
        List of error messages. Empty if valid.

    Raises:
        FileNotFoundError: If xml_path or xsd_path does not exist.
        etree.XMLSyntaxError: If the XML is not well-formed.
    """
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")
    if not xsd_path.exists():
        raise FileNotFoundError(f"XSD file not found: {xsd_path}")

    xsd_doc = etree.parse(str(xsd_path))
    schema = etree.XMLSchema(xsd_doc)

    xml_doc = etree.parse(str(xml_path))
    is_valid = schema.validate(xml_doc)

    if is_valid:
        return []

    return [str(err) for err in schema.error_log]


def main() -> None:
    """CLI entry point for XML validation."""
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Validate book.xml against XSD schema",
    )
    parser.add_argument(
        "xml_path",
        type=Path,
        help="Path to the book.xml file",
    )
    parser.add_argument(
        "--xsd",
        type=Path,
        default=DEFAULT_XSD_PATH,
        help=f"Path to XSD schema (default: {DEFAULT_XSD_PATH})",
    )

    args = parser.parse_args()

    try:
        errors = validate_xml(args.xml_path, args.xsd)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    except etree.XMLSyntaxError as e:
        logger.error("XML is not well-formed: %s", e)
        sys.exit(1)

    if errors:
        logger.error("Validation FAILED with %d error(s):", len(errors))
        for err in errors:
            logger.error("  %s", err)
        sys.exit(1)

    logger.info("Validation passed: %s", args.xml_path)


if __name__ == "__main__":
    main()
