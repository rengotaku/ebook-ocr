# Phase 1: Setup Output

**Status**: Completed
**Date**: 2026-02-09

## Existing Implementation Analysis

### 1. models.py - Data Classes

**Key Classes**:
- `TocEntry`: dataclass with `level` (str), `number` (str), `title` (str)
- `TableOfContents`: dataclass with `entries` (list[TocEntry]), `begin` (int), `end` (int)
- `PageMetadata`: dataclass with `type` (str), `content` (str), `read_aloud` (bool)
- `Page`: dataclass with `number`, `source_file`, `announcement`, `content`, `figures`, `metadata`
- `Book`: dataclass with `metadata`, `toc`, `pages`

**Observations**:
- TOC structure already parsed and available in `Book.toc`
- `TocEntry.level` is string: "chapter", "section", "subsection"
- `TocEntry.number` is string: "1", "2.1", "2.1.1" etc.
- `PageMetadata.content` contains section info like "1.1 SREの概要 ― 1 / 3"

### 2. xml_builder.py - XML Generation

**Functions**:
- `build_xml(book: Book) -> str`: Builds XML from Book model
- `insert_error_comment(...)`: Adds error comments
- `build_xml_with_errors(...)`: Combined function

**Observations**:
- Currently generates flat page structure (no hierarchical grouping)
- Uses xml.etree.ElementTree
- TOC is rendered as flat `<entry>` elements

### 3. cli.py - CLI Interface

**Functions**:
- `parse_args()`: Argument parsing
- `convert_book(...)`: Main conversion logic
- `main()`: Entry point

**Current Options**:
- Input/output file handling
- Error handling flags

**Integration Point**: Add `--group-pages` option here

### 4. Existing Tests

**Test Files**:
- `test_cli.py`: CLI tests
- `test_e2e.py`: End-to-end tests
- `test_e2e_toc.py`: TOC-related E2E tests
- `test_integration.py`: Integration tests
- `test_parser.py`: Parser tests
- `test_schema_validation.py`: Schema tests
- `test_transformer.py`: Transformer tests
- `test_xml_builder.py`: XML builder tests

**Test Pattern**: pytest with fixtures, uses sample data

### 5. book.xml Structure Analysis

**Key XML Elements**:
```xml
<book>
  <metadata><title>Converted Book</title></metadata>
  <toc begin="7" end="13">
    <entry level="chapter" number="1" title="SREとは" />
    <entry level="section" number="2.1" title="SLOを理解するための..." />
    <entry level="subsection" number="2.1.1" title="SLA" />
    ...
  </toc>
  <page number="1" sourceFile="page_0001.png">
    <pageMetadata type="chapter-page" readAloud="false">1 / 1</pageMetadata>
    ...
  </page>
  ...
</book>
```

**PageMetadata Patterns**:
- `1 / 1` - Simple page/total
- `<emphasis>はじめに</emphasis> 1 / 3` - Front-matter with title
- `第1章 SREとは — 1 / 1` - Chapter title page
- `1.1 SREの概要 ― 1 / 3` - Section page with number
- `1.1.4 ソフト... ― 3 / 3` - Subsection with number
- `1.2.2 過剰な... ― 4 / 5` - Subsection

**Section Number Extraction Regex**:
```python
# Pattern: "X.Y.Z タイトル — N / M"
# Capture group: section number at start
r'^(\d+(?:\.\d+)*)(?:\s|[.\-])'
```

**TOC Range**:
- `begin="7"`, `end="13"` - Pages 7-13 are TOC pages
- Pages before `begin` (1-6) = front-matter
- Page 14+ = chapters begin

## Key Implementation Decisions

### New File: `src/book_converter/page_grouper.py`

**Data Classes**:
```python
@dataclass
class SectionNumber:
    parts: tuple[int, ...]  # (1,) or (2, 1) or (2, 1, 1)

@dataclass
class TOCEntry:
    level: str  # "chapter", "section", "subsection"
    number: str  # "1", "2.1", "2.1.1"
    title: str
    parsed_number: SectionNumber | None
```

**Functions to Implement**:
1. `parse_section_number(s: str) -> SectionNumber | None`
2. `extract_section_from_metadata(metadata: str) -> str | None`
3. `extract_section_from_heading(heading: str) -> str | None`
4. `parse_toc(toc_element: Element) -> list[TOCEntry]`
5. `assign_pages_to_sections(pages, toc_entries, toc_begin, toc_end) -> dict`
6. `build_hierarchy(book_element, page_assignments) -> Element`
7. `group_pages_by_toc(input_xml: str) -> str`

### Output Structure Target

```xml
<book>
  <metadata>...</metadata>
  <toc>...</toc>
  <front-matter>
    <page number="1">...</page>
    ...
    <page number="6">...</page>
  </front-matter>
  <chapter number="1" title="SREとは">
    <page number="14" type="chapter-title">...</page>
    <section number="1.1" title="SREの概要">
      <page number="15">...</page>
      <page number="16">...</page>
      <page number="17">...</page>
    </section>
    <section number="1.2" title="なぜSREが重要なのか">
      ...
    </section>
  </chapter>
  <chapter number="2" title="信頼性を定義して...">
    ...
  </chapter>
</book>
```

## Ready for Phase 2

- All existing code understood
- XML structure analyzed
- Section number patterns identified
- New module location confirmed
- Output structure designed
