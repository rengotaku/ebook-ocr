"""E2E tests for book markdown to XML conversion.

Tests for Phase 5: CLI & Error Handling
- T072: E2E test (sample_book.md -> expected_book.xml comparison)
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest


class TestE2EConversion:
    """T072: E2Eテスト (sample_book.md -> expected_book.xml 比較)"""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def sample_book_md(self, fixtures_dir: Path) -> Path:
        """Get sample_book.md path."""
        return fixtures_dir / "sample_book.md"

    @pytest.fixture
    def expected_book_xml(self, fixtures_dir: Path) -> Path:
        """Get expected_book.xml path."""
        return fixtures_dir / "expected_book.xml"

    def test_sample_files_exist(
        self, sample_book_md: Path, expected_book_xml: Path
    ) -> None:
        """サンプルファイルが存在する"""
        assert sample_book_md.exists(), f"sample_book.md not found at {sample_book_md}"
        assert expected_book_xml.exists(), f"expected_book.xml not found at {expected_book_xml}"

    def test_convert_sample_book(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """sample_book.mdを変換できる"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"

        result = convert_book(sample_book_md, output_file)

        assert result.success is True
        assert output_file.exists()

    def test_output_is_valid_xml(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """出力が有効なXMLである"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        content = output_file.read_text(encoding="utf-8")

        # XML宣言を含む
        assert "<?xml" in content

        # 有効なXMLとしてパースできる
        tree = ET.parse(output_file)
        root = tree.getroot()
        assert root is not None

    def test_output_has_book_root_element(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """出力にbook要素がある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        assert root.tag == "book"

    def test_output_has_metadata(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """出力にmetadataがある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        metadata = root.find("metadata")
        assert metadata is not None

    def test_output_has_pages(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """出力にページがある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        pages = root.findall("page")
        assert len(pages) > 0

    def test_output_page_count_matches_input(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """出力のページ数が入力と一致"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        # Count pages in input
        input_content = sample_book_md.read_text(encoding="utf-8")
        import re
        input_page_count = len(re.findall(r"--- Page \d+ \([^)]+\) ---", input_content))

        tree = ET.parse(output_file)
        root = tree.getroot()
        pages = root.findall("page")

        assert len(pages) == input_page_count

    def test_pages_have_number_attribute(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """ページにnumber属性がある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()
        pages = root.findall("page")

        for page in pages:
            assert "number" in page.attrib

    def test_pages_have_source_file_attribute(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """ページにsourceFile属性がある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()
        pages = root.findall("page")

        for page in pages:
            assert "sourceFile" in page.attrib

    def test_pages_have_page_announcement(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """ページにpageAnnouncementがある"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()
        pages = root.findall("page")

        for page in pages:
            announcement = page.find("pageAnnouncement")
            assert announcement is not None, f"Page {page.get('number')} missing pageAnnouncement"

    def test_xpath_query_for_page(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """XPathでページを検索できる"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        # XPath: //page[@number='1']
        page_1 = root.find(".//page[@number='1']")
        assert page_1 is not None, "Page 1 not found by XPath"

    def test_xpath_query_for_heading(
        self, sample_book_md: Path, tmp_path: Path
    ) -> None:
        """XPathで見出しを検索できる"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        tree = ET.parse(output_file)
        root = tree.getroot()

        # Find heading with level 1
        heading = root.find(".//heading[@level='1']")
        assert heading is not None, "Heading level 1 not found"


class TestE2EComparison:
    """E2E出力比較テスト"""

    @pytest.fixture
    def fixtures_dir(self) -> Path:
        """Get the fixtures directory path."""
        return Path(__file__).parent / "fixtures"

    @pytest.fixture
    def sample_book_md(self, fixtures_dir: Path) -> Path:
        """Get sample_book.md path."""
        return fixtures_dir / "sample_book.md"

    @pytest.fixture
    def expected_book_xml(self, fixtures_dir: Path) -> Path:
        """Get expected_book.xml path."""
        return fixtures_dir / "expected_book.xml"

    def test_output_matches_expected_page_count(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力のページ数が期待値と一致"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_pages = expected_tree.getroot().findall("page")
        actual_pages = actual_tree.getroot().findall("page")

        assert len(actual_pages) == len(expected_pages)

    def test_output_matches_expected_page_numbers(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力のページ番号が期待値と一致"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_numbers = [p.get("number") for p in expected_tree.getroot().findall("page")]
        actual_numbers = [p.get("number") for p in actual_tree.getroot().findall("page")]

        assert actual_numbers == expected_numbers

    def test_output_matches_expected_source_files(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力のソースファイルが期待値と一致"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_files = [p.get("sourceFile") for p in expected_tree.getroot().findall("page")]
        actual_files = [p.get("sourceFile") for p in actual_tree.getroot().findall("page")]

        assert actual_files == expected_files

    def test_output_matches_expected_headings(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力の見出しが期待値と一致"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_headings = [
            (h.get("level"), h.text)
            for h in expected_tree.getroot().findall(".//heading")
        ]
        actual_headings = [
            (h.get("level"), h.text)
            for h in actual_tree.getroot().findall(".//heading")
        ]

        assert actual_headings == expected_headings

    def test_output_contains_figures(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力に図が含まれる"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_figures = expected_tree.getroot().findall(".//figure")
        actual_figures = actual_tree.getroot().findall(".//figure")

        assert len(actual_figures) == len(expected_figures)

    def test_output_contains_page_metadata(
        self, sample_book_md: Path, expected_book_xml: Path, tmp_path: Path
    ) -> None:
        """出力にページメタデータが含まれる"""
        from src.book_converter.cli import convert_book

        output_file = tmp_path / "output.xml"
        convert_book(sample_book_md, output_file)

        expected_tree = ET.parse(expected_book_xml)
        actual_tree = ET.parse(output_file)

        expected_metadata = expected_tree.getroot().findall(".//pageMetadata")
        actual_metadata = actual_tree.getroot().findall(".//pageMetadata")

        assert len(actual_metadata) == len(expected_metadata)


class TestE2EEdgeCases:
    """E2Eエッジケーステスト"""

    def test_empty_file(self, tmp_path: Path) -> None:
        """空のファイルを処理"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "empty.md"
        input_file.write_text("")

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        # 空ファイルでも有効なXMLを生成
        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "<book>" in content

    def test_single_page(self, tmp_path: Path) -> None:
        """1ページのファイルを処理"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "single.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        tree = ET.parse(output_file)
        pages = tree.getroot().findall("page")
        assert len(pages) == 1

    def test_unicode_content(self, tmp_path: Path) -> None:
        """Unicode文字を含むファイルを処理"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "unicode.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "# 日本語タイトル\n\n"
            "日本語の本文。特殊文字: 「」『』\n",
            encoding="utf-8"
        )

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        assert "日本語タイトル" in content
        assert "「」『』" in content

    def test_many_pages(self, tmp_path: Path) -> None:
        """多くのページを含むファイルを処理"""
        from src.book_converter.cli import convert_book

        lines = []
        for i in range(1, 101):
            lines.append(f"--- Page {i} (page_{i:04d}.png) ---\n")
            lines.append(f"\n## Chapter {i}\n\nContent for page {i}.\n\n")

        input_file = tmp_path / "many_pages.md"
        input_file.write_text("".join(lines))

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        tree = ET.parse(output_file)
        pages = tree.getroot().findall("page")
        assert len(pages) == 100

    def test_deep_heading_warning_in_output(self, tmp_path: Path) -> None:
        """4階層以上の見出し警告がXMLコメントで出力される"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "deep_heading.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "#### Deep Heading\n\n"  # Level 4 should trigger warning
            "Content\n"
        )

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        # 4階層警告がコメントとして含まれる
        assert "ERROR" in content or "WARNING" in content or "階層" in content
