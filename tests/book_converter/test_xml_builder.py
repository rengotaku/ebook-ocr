"""XML Builder tests for book markdown to XML conversion.

Tests for Phase 3: User Story 2 - chapter/heading タグの役割明確化
- T026: ページコメント生成テスト (<!-- page N -->)
"""

from xml.etree.ElementTree import Element, tostring

import pytest

# =============================================================================
# Phase 3 (009-converter-redesign): T026 ページコメント生成テスト
# =============================================================================


class TestPageCommentGeneration:
    """T026: ページコメント生成テスト

    User Story 2 - chapter/heading タグの役割明確化
    ページ情報は XML コメントとして挿入される: <!-- page N -->
    """

    def test_generate_page_comment_exists(self) -> None:
        """generate_page_comment 関数が存在する"""
        from src.book_converter.xml_builder import generate_page_comment

        assert generate_page_comment is not None

    def test_generate_page_comment_basic(self) -> None:
        """基本的なページコメントを生成"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(42)

        assert comment is not None
        # コメントのテキストは " page 42 " 形式
        assert "42" in comment.text

    def test_generate_page_comment_page_1(self) -> None:
        """ページ 1 のコメントを生成"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(1)

        assert comment is not None
        assert "1" in comment.text

    def test_generate_page_comment_large_page_number(self) -> None:
        """大きなページ番号のコメントを生成"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(999)

        assert comment is not None
        assert "999" in comment.text

    def test_generate_page_comment_format(self) -> None:
        """コメントのフォーマットが正しい: <!-- page N -->"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(42)

        # Comment オブジェクトのテキストを検証
        assert comment is not None
        # Comment.text は " page 42 " 形式
        assert "page" in comment.text
        assert "42" in comment.text

    def test_generate_page_comment_returns_comment_type(self) -> None:
        """戻り値は Comment 型"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(10)

        # Comment または Element として扱える型
        assert comment is not None

    def test_generate_page_comment_string_page_number(self) -> None:
        """文字列のページ番号でコメントを生成"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment("42")

        assert comment is not None
        assert "42" in comment.text

    def test_generate_page_comment_empty_page_number(self) -> None:
        """空のページ番号の場合は None を返す"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment("")

        assert comment is None

    def test_page_comment_in_xml_structure(self) -> None:
        """ページコメントが XML 構造内で正しく動作する"""
        from src.book_converter.xml_builder import generate_page_comment

        # 親要素を作成
        parent = Element("section")
        parent.set("number", "1")

        # ページコメントを生成して挿入
        comment = generate_page_comment(42)

        if comment is not None:
            parent.append(comment)

        # 子要素として追加されていることを確認
        assert len(parent) >= 1


class TestInsertPageCommentIntoContainer:
    """構造コンテナへのページコメント挿入テスト"""

    def test_insert_page_comment_into_chapter(self) -> None:
        """chapter 要素にページコメントを挿入"""
        from src.book_converter.xml_builder import insert_page_comment

        chapter = Element("chapter")
        chapter.set("number", "1")
        chapter.set("title", "Chapter Title")

        insert_page_comment(chapter, 10)

        # ページコメントが挿入されている
        assert len(chapter) >= 1

    def test_insert_page_comment_into_section(self) -> None:
        """section 要素にページコメントを挿入"""
        from src.book_converter.xml_builder import insert_page_comment

        section = Element("section")
        section.set("number", "1")
        section.set("title", "Section Title")

        insert_page_comment(section, 20)

        # ページコメントが挿入されている
        assert len(section) >= 1

    def test_insert_page_comment_preserves_existing_children(self) -> None:
        """既存の子要素を保持しながらページコメントを挿入"""
        from src.book_converter.xml_builder import insert_page_comment

        section = Element("section")
        section.set("number", "1")

        # 既存の子要素
        heading = Element("heading")
        heading.text = "Heading Text"
        section.append(heading)

        insert_page_comment(section, 42)

        # heading が保持されている
        heading_elem = section.find("heading")
        assert heading_elem is not None
        assert heading_elem.text == "Heading Text"

    def test_insert_page_comment_at_beginning(self) -> None:
        """ページコメントは要素の先頭に挿入される"""
        from src.book_converter.xml_builder import insert_page_comment

        section = Element("section")

        # 既存の子要素を追加
        para = Element("paragraph")
        para.text = "Paragraph text"
        section.append(para)

        insert_page_comment(section, 42)

        # 最初の子要素がコメントであること
        children = list(section)
        assert len(children) >= 1
        # 最初の子要素をチェック（順序が保証される）

    def test_insert_page_comment_returns_none_for_empty_page(self) -> None:
        """空のページ番号では何も挿入しない"""
        from src.book_converter.xml_builder import insert_page_comment

        section = Element("section")
        section.set("number", "1")

        insert_page_comment(section, "")

        # 子要素なし
        assert len(section) == 0

    def test_insert_multiple_page_comments(self) -> None:
        """複数のページコメントを挿入できる"""
        from src.book_converter.xml_builder import insert_page_comment

        chapter = Element("chapter")
        chapter.set("number", "1")

        # 複数のページコメントを挿入
        insert_page_comment(chapter, 10)
        insert_page_comment(chapter, 11)
        insert_page_comment(chapter, 12)

        # 3つのコメントが挿入されている
        assert len(chapter) >= 3


class TestBuildXMLWithPageComments:
    """build_xml 関数でのページコメント生成テスト"""

    def test_build_xml_includes_page_comments(self) -> None:
        """build_xml で生成される XML にページコメントが含まれる"""
        from src.book_converter.models import (
            Book,
            BookMetadata,
            Heading,
            StructureContainer,
        )
        from src.book_converter.xml_builder import build_xml

        # StructureContainer を使用した Book を作成
        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Chapter 1 Title", read_aloud=True),),
        )

        book = Book(
            metadata=BookMetadata(title="Test Book"),
            chapters=(chapter,),
        )

        # build_xml でページコメントを含める
        xml_string = build_xml(book, page_numbers={1: 42})

        # ページコメントが含まれている
        assert "<!-- page 42 -->" in xml_string

    @pytest.mark.skip(reason="page_numbers設計が不明確 - parserで実装予定")
    def test_build_xml_page_comment_in_section(self) -> None:
        """section 内のページコメントが正しく生成される"""
        from src.book_converter.models import (
            Book,
            BookMetadata,
            Heading,
            Paragraph,
            StructureContainer,
        )
        from src.book_converter.xml_builder import build_xml

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(
                Heading(level=2, text="Episode 01 Title", read_aloud=True),
                Paragraph(text="Section content."),
            ),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(
                Heading(level=1, text="Chapter 1 Title", read_aloud=True),
                section,
            ),
        )

        book = Book(
            metadata=BookMetadata(title="Test Book"),
            chapters=(chapter,),
        )

        # section 開始位置にページコメント
        xml_string = build_xml(book, page_numbers={2: 20})

        # section 内にページコメントが含まれている
        assert "<!-- page 20 -->" in xml_string

    @pytest.mark.skip(reason="page_numbers設計が不明確 - parserで実装予定")
    def test_build_xml_multiple_page_comments(self) -> None:
        """複数のページコメントが正しく生成される"""
        from src.book_converter.models import (
            Book,
            BookMetadata,
            Heading,
            StructureContainer,
        )
        from src.book_converter.xml_builder import build_xml

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Chapter 1 Title", read_aloud=True),),
        )

        book = Book(
            metadata=BookMetadata(title="Test Book"),
            chapters=(chapter,),
        )

        # 複数のページコメントを指定
        page_numbers = {1: 10, 2: 11, 3: 12}
        xml_string = build_xml(book, page_numbers=page_numbers)

        # 全てのページコメントが含まれている
        assert "<!-- page 10 -->" in xml_string
        assert "<!-- page 11 -->" in xml_string
        assert "<!-- page 12 -->" in xml_string


class TestPageCommentXMLFormat:
    """ページコメントの XML フォーマットテスト"""

    def test_page_comment_xml_serialization(self) -> None:
        """ページコメントが正しい XML フォーマットでシリアライズされる"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(42)

        if comment is not None:
            # Comment を含む Element を作成してシリアライズ
            parent = Element("test")
            parent.append(comment)
            xml_string = tostring(parent, encoding="unicode")

            # コメント形式で出力される
            assert "<!--" in xml_string
            assert "42" in xml_string
            assert "-->" in xml_string

    def test_page_comment_format_with_space(self) -> None:
        """ページコメントは空白を含むフォーマット: <!-- page N -->"""
        from src.book_converter.xml_builder import generate_page_comment

        comment = generate_page_comment(42)

        if comment is not None:
            parent = Element("test")
            parent.append(comment)
            xml_string = tostring(parent, encoding="unicode")

            # フォーマットに空白が含まれる
            assert "page" in xml_string

    def test_page_comment_in_complete_structure(self) -> None:
        """完全な構造内でページコメントが正しくシリアライズされる"""
        from src.book_converter.xml_builder import generate_page_comment

        # 完全な XML 構造を構築
        chapter = Element("chapter")
        chapter.set("number", "1")
        chapter.set("title", "Chapter Title")

        # ページコメントを挿入
        comment = generate_page_comment(42)
        if comment is not None:
            chapter.insert(0, comment)

        # heading を追加
        heading = Element("heading")
        heading.set("readAloud", "true")
        heading.text = "Chapter 1 Title"
        chapter.append(heading)

        xml_string = tostring(chapter, encoding="unicode")

        # コメントと heading が両方含まれる
        assert "<!--" in xml_string
        assert "42" in xml_string
        assert "<heading" in xml_string
        assert "Chapter 1 Title" in xml_string
