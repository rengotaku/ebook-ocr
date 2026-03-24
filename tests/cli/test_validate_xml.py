"""Tests for src.cli.validate_xml module."""

from pathlib import Path

import pytest

from src.cli.validate_xml import DEFAULT_XSD_PATH, validate_xml

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "book_converter" / "fixtures"


class TestValidateXml:
    """Tests for validate_xml function."""

    def test_valid_fixture_passes(self) -> None:
        xml_path = FIXTURE_DIR / "expected_book.xml"
        errors = validate_xml(xml_path, DEFAULT_XSD_PATH)
        assert errors == []

    def test_invalid_xml_returns_errors(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "bad.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?><book><unknown_tag/></book>',
            encoding="utf-8",
        )
        errors = validate_xml(xml_path, DEFAULT_XSD_PATH)
        assert len(errors) > 0
        assert "unknown_tag" in errors[0]

    def test_missing_required_attribute(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "missing_attr.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<book><metadata><title>Test</title></metadata>"
            '<page number="1"><content/></page></book>',
            encoding="utf-8",
        )
        errors = validate_xml(xml_path, DEFAULT_XSD_PATH)
        assert len(errors) > 0
        assert "sourceFile" in errors[0]

    def test_xml_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="XML file not found"):
            validate_xml(tmp_path / "nonexistent.xml", DEFAULT_XSD_PATH)

    def test_xsd_file_not_found(self, tmp_path: Path) -> None:
        xml_path = FIXTURE_DIR / "expected_book.xml"
        with pytest.raises(FileNotFoundError, match="XSD file not found"):
            validate_xml(xml_path, tmp_path / "nonexistent.xsd")

    def test_malformed_xml(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "malformed.xml"
        xml_path.write_text("<book><unclosed>", encoding="utf-8")
        from lxml import etree

        with pytest.raises(etree.XMLSyntaxError):
            validate_xml(xml_path, DEFAULT_XSD_PATH)

    def test_valid_modern_format(self, tmp_path: Path) -> None:
        xml_path = tmp_path / "modern.xml"
        xml_path.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<book>"
            "<metadata><title>Test</title></metadata>"
            '<chapter title="Ch1">'
            '<section title="S1">'
            "<paragraph>text</paragraph>"
            "</section>"
            "</chapter>"
            "</book>",
            encoding="utf-8",
        )
        errors = validate_xml(xml_path, DEFAULT_XSD_PATH)
        assert errors == []

    def test_xsd_file_exists(self) -> None:
        assert DEFAULT_XSD_PATH.exists(), f"XSD file missing: {DEFAULT_XSD_PATH}"
