# Refactoring Map: Pylintエラー対応

**Date**: 2026-02-19
**Branch**: `012-fix-pylint-errors`

## 分割マップ概要

```
src/
├── book_converter/
│   ├── parser.py (1739行)
│   │   └── → parser/
│   │       ├── __init__.py    # 公開API再エクスポート
│   │       ├── toc.py         # TOC解析
│   │       ├── page.py        # ページ解析
│   │       ├── heading.py     # 見出し解析
│   │       ├── paragraph.py   # 段落解析
│   │       ├── figure.py      # 図表・リスト解析
│   │       ├── utils.py       # ユーティリティ
│   │       └── models.py      # StructureHeading等
│   │
│   ├── page_grouper.py (1148行)
│   │   └── → page_grouper/
│   │       ├── __init__.py    # 公開API再エクスポート
│   │       ├── section.py     # セクション解析
│   │       ├── toc.py         # TOC処理
│   │       ├── assignment.py  # ページ割当
│   │       ├── hierarchy.py   # 階層構築
│   │       ├── xml.py         # XML変換
│   │       └── models.py      # FlattenStats, SectionNumber, TOCEntry
│   │
│   └── transformer.py (566行)
│       └── → transformer.py + transformer_utils.py
│
├── layout_ocr.py (595行)
│   └── → layout_ocr.py + layout_ocr_utils.py
│
├── ocr_integrated.py (577行)
│   └── → ocr_integrated.py + ocr_integrated_utils.py
│
├── ocr_yomitoku.py (535行)
│   └── → ocr_yomitoku.py + yomitoku_io.py + yomitoku_layout.py
│
└── rover/
    └── ensemble.py (593行)
        └── → ensemble.py + line_processing.py
```

---

## 詳細分割計画

### 1. parser/ パッケージ

#### parser/__init__.py
```python
"""Book parser package - maintains backward compatibility."""
from .toc import (
    parse_toc_marker,
    parse_content_marker,
    normalize_toc_line,
    merge_toc_lines,
    normalize_toc_text,
    split_toc_entries,
    parse_toc_lines,
    parse_toc_entry,
)
from .page import (
    parse_page_marker,
    extract_page_number,
    create_page_announcement,
    parse_page_metadata,
    parse_pages,
    parse_pages_with_errors,
)
from .heading import (
    parse_structure_heading,
    parse_heading,
    parse_heading_with_warning,
)
from .paragraph import (
    parse_paragraph_lines,
    split_paragraphs,
    merge_continuation_paragraphs,
    parse_paragraph,
)
from .figure import (
    parse_list,
    parse_figure_comment,
    parse_figure_placeholder,
    parse_figure,
)
from .utils import (
    is_list_line,
    get_read_aloud_from_stack,
    count_markers,
)
from .models import StructureHeading

__all__ = [
    # TOC
    "parse_toc_marker", "parse_content_marker", "normalize_toc_line",
    "merge_toc_lines", "normalize_toc_text", "split_toc_entries",
    "parse_toc_lines", "parse_toc_entry",
    # Page
    "parse_page_marker", "extract_page_number", "create_page_announcement",
    "parse_page_metadata", "parse_pages", "parse_pages_with_errors",
    # Heading
    "parse_structure_heading", "parse_heading", "parse_heading_with_warning",
    # Paragraph
    "parse_paragraph_lines", "split_paragraphs",
    "merge_continuation_paragraphs", "parse_paragraph",
    # Figure
    "parse_list", "parse_figure_comment", "parse_figure_placeholder", "parse_figure",
    # Utils
    "is_list_line", "get_read_aloud_from_stack", "count_markers",
    # Models
    "StructureHeading",
]
```

#### 各モジュールの責務

| モジュール | 責務 | 推定行数 |
|-----------|------|----------|
| toc.py | TOCマーカー解析、正規化、エントリ分割 | ~400 |
| page.py | ページマーカー、メタデータ、ページ解析 | ~350 |
| heading.py | 見出し解析、構造見出し | ~200 |
| paragraph.py | 段落解析、結合、分割 | ~250 |
| figure.py | 図表、リスト解析 | ~200 |
| utils.py | 共通ユーティリティ | ~100 |
| models.py | StructureHeading クラス | ~50 |

---

### 2. page_grouper/ パッケージ

#### page_grouper/__init__.py
```python
"""Page grouper package - maintains backward compatibility."""
from .section import (
    parse_section_number,
    normalize_for_matching,
    extract_section_from_page_metadata,
    extract_section_from_heading,
    is_chapter_title_page,
)
from .toc import parse_toc, validate_page_count
from .assignment import (
    group_pages_by_toc,
    _assign_pages_to_sections,
    _assign_pages_to_sections_new,
)
from .hierarchy import (
    _find_first_chapter,
    _build_hierarchical_structure,
    _add_sections_to_chapter,
    _build_chapters,
    _build_sections,
    _pages_to_section,
)
from .xml import _serialize_to_xml, convert_pages_to_book
from .models import FlattenStats, SectionNumber, TOCEntry

__all__ = [
    # Section
    "parse_section_number", "normalize_for_matching",
    "extract_section_from_page_metadata", "extract_section_from_heading",
    "is_chapter_title_page",
    # TOC
    "parse_toc", "validate_page_count",
    # Assignment
    "group_pages_by_toc",
    # Hierarchy
    "_build_hierarchical_structure", "_build_chapters", "_build_sections",
    # XML
    "_serialize_to_xml", "convert_pages_to_book",
    # Models
    "FlattenStats", "SectionNumber", "TOCEntry",
]
```

---

### 3. ヘルパー抽出マップ

#### layout_ocr_utils.py
```python
# From layout_ocr.py
def is_title(region) -> bool: ...
def calc_non_char_ratio(text: str) -> float: ...
def is_low_quality(text: str) -> bool: ...
def crop_region(image, bbox) -> Image: ...
def calculate_coverage(regions, image_size) -> float: ...
def should_fallback(result) -> bool: ...
def format_ocr_result(result) -> str: ...
def select_ocr_engine(region) -> str: ...
```

#### ocr_integrated_utils.py
```python
# From ocr_integrated.py
def filter_overlapping_regions(regions) -> list: ...
def group_text_by_regions(texts, regions) -> dict: ...
def structure_text_by_paragraphs(text: str) -> list: ...
def extract_titles_from_regions(regions) -> list: ...
def structure_text_with_titles(text: str, titles: list) -> str: ...
def select_best_engine(results: dict) -> str: ...
```

#### rover/line_processing.py
```python
# From rover/ensemble.py
def is_garbage(text: str) -> bool: ...
def normalize_confidence(conf: float) -> float: ...
def split_multiline_items(items: list) -> list: ...
def cluster_lines_by_y(lines: list) -> list: ...
def align_lines_by_y(line_groups: list) -> list: ...
```

#### yomitoku_io.py
```python
# From ocr_yomitoku.py
def save_yomitoku_results(results, path): ...
def load_yomitoku_results(path) -> dict: ...
def reset_analyzer(): ...
```

#### yomitoku_layout.py
```python
# From ocr_yomitoku.py
def paragraphs_to_layout(paragraphs) -> dict: ...
def visualize_layout(image, layout) -> Image: ...
def detect_layout_yomitoku(image) -> dict: ...
```

---

## 関数リファクタリングマップ

### 高優先度（複数違反）

| 関数 | ファイル | 違反 | 戦略 |
|------|----------|------|------|
| `parse_pages_with_errors` | parser.py:465 | locals:20, branches:22, statements:70 | ヘルパー抽出 + 早期リターン |
| `_parse_single_page_content` | parser.py:1316 | locals:29, branches:14, statements:57 | dataclass化 + 分割 |
| `run_integrated_ocr` | ocr_integrated.py:344 | locals:26, branches:15, statements:65 | ヘルパー抽出 + 設定dataclass |
| `group_pages_by_toc` | page_grouper.py:449 | locals:28, statements:53 | 処理段階ごとに分割 |
| `run_layout_ocr` | layout_ocr.py:485 | locals:28, statements:60 | ヘルパー抽出 |

### 中優先度（単一違反・軽微）

| 関数 | ファイル | 違反 | 戦略 |
|------|----------|------|------|
| `ocr_by_layout` | layout_ocr.py:354 | locals:24 | ヘルパー抽出 |
| `visualize_layout` | ocr_yomitoku.py:430 | locals:23 | 描画処理を分離 |
| `cluster_lines_by_y` | rover/ensemble.py:246 | locals:19 | dataclass化 |
| `align_lines_by_y` | rover/ensemble.py:360 | locals:19 | dataclass化 |

---

## 依存関係マップ

```
parser/
├── models.py (依存なし)
├── utils.py ← models.py
├── toc.py ← utils.py, models.py
├── heading.py ← models.py
├── paragraph.py ← utils.py
├── figure.py ← utils.py
└── page.py ← toc.py, heading.py, paragraph.py, figure.py

page_grouper/
├── models.py (依存なし)
├── section.py ← models.py
├── toc.py ← models.py
├── assignment.py ← section.py, models.py
├── hierarchy.py ← section.py, models.py
└── xml.py ← models.py
```

**循環インポートリスク**: 低（依存方向が一方向）

---

## テスト影響マップ

| 分割対象 | 影響テスト | 更新内容 |
|----------|-----------|----------|
| parser → parser/ | tests/test_parser.py | import文のみ（`__init__.py`で再エクスポート） |
| page_grouper → page_grouper/ | tests/test_page_grouper.py | import文のみ |
| layout_ocr.py分割 | tests/test_layout_ocr.py | 変更なし（内部分割） |
| rover/ensemble.py分割 | tests/test_rover.py | 変更なし |

---

## 実装順序

```
Phase 2: 大規模ファイル分割
├── Step 1: parser/ パッケージ化
│   ├── models.py 作成
│   ├── utils.py 作成
│   ├── 各モジュール作成（依存順）
│   ├── __init__.py 作成
│   ├── 元parser.py削除
│   └── pytest確認
│
└── Step 2: page_grouper/ パッケージ化
    └── (同様の手順)

Phase 3: 中規模ファイル分割
├── layout_ocr_utils.py 抽出
├── ocr_integrated_utils.py 抽出
├── yomitoku_io.py + yomitoku_layout.py 抽出
└── rover/line_processing.py 抽出

Phase 4: 関数リファクタリング
├── 高優先度関数 (5関数)
└── 中優先度関数 (残り)

Phase 5: 検証 & Polish
├── pylint全チェック
├── pytest全パス確認
└── pre-commit有効化
```
