# Research: Pylintエラー対応

**Date**: 2026-02-19
**Branch**: `012-fix-pylint-errors`

## 分析サマリ

### 違反概要

| 違反タイプ | 件数 | 制限値 |
|-----------|------|--------|
| C0302 (too-many-lines) | 7ファイル | 500行 |
| R0914 (too-many-locals) | 26箇所 | 15変数 |
| R0915 (too-many-statements) | 6箇所 | 50文 |
| R0912 (too-many-branches) | 6箇所 | 12分岐 |

---

## ファイル分析

### 1. src/book_converter/parser.py (1739行)

**シンボル構成**:
- Constants: 3 (`TOC_CLASSIFIER_AVAILABLE`, `BULLET_MARKERS`, `ORDERED_LIST_PATTERN`)
- Classes: 1 (`StructureHeading`)
- Functions: 29

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| TOC解析 | `parse_toc_*`, `normalize_toc_*`, `merge_toc_*`, `split_toc_*` | ~400行 | `parser/toc.py` |
| ページ解析 | `parse_page_*`, `extract_page_*`, `create_page_*`, `parse_pages*` | ~350行 | `parser/page.py` |
| 見出し解析 | `parse_heading*`, `parse_structure_heading` | ~200行 | `parser/heading.py` |
| 段落解析 | `parse_paragraph*`, `split_paragraphs`, `merge_continuation_*` | ~250行 | `parser/paragraph.py` |
| 図表解析 | `parse_figure*`, `parse_list` | ~200行 | `parser/figure.py` |
| ユーティリティ | `is_list_line`, `count_markers`, `get_read_aloud_from_stack` | ~100行 | `parser/utils.py` |
| Classes | `StructureHeading` | ~50行 | `parser/models.py` |

**推奨アクション**: パッケージ化 (`parser/` ディレクトリ)

**違反関数**:
- `parse_pages_with_errors` (L465): 20 locals, 22 branches, 70 statements
- `_parse_single_page_content` (L1316): 29 locals, 14 branches, 57 statements
- `:241` 関数: 18 branches

---

### 2. src/book_converter/page_grouper.py (1148行)

**シンボル構成**:
- Classes: 3 (`FlattenStats`, `SectionNumber`, `TOCEntry`)
- Functions: 26

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| セクション解析 | `parse_section_*`, `extract_section_*`, `_extract_*` | ~250行 | `page_grouper/section.py` |
| TOC処理 | `parse_toc`, `validate_page_count` | ~150行 | `page_grouper/toc.py` |
| ページ割当 | `_assign_pages_*`, `group_pages_*`, `_flatten_*` | ~300行 | `page_grouper/assignment.py` |
| 階層構築 | `_build_*`, `_add_sections_*` | ~250行 | `page_grouper/hierarchy.py` |
| XML変換 | `_serialize_to_xml`, `convert_pages_to_book` | ~100行 | `page_grouper/xml.py` |
| モデル | Classes + ユーティリティ | ~100行 | `page_grouper/models.py` |

**推奨アクション**: パッケージ化 (`page_grouper/` ディレクトリ)

**違反関数**:
- `group_pages_by_toc` (L449): 28 locals, 53 statements
- `_build_hierarchical_structure` (L732): 17 branches

---

### 3. src/layout_ocr.py (595行)

**シンボル構成**:
- Classes: 1 (`OCRResult`)
- Functions: 14

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| OCR実行 | `ocr_*`, `run_*` | ~200行 | 維持 |
| 品質判定 | `is_title`, `is_low_quality`, `calc_non_char_ratio` | ~100行 | `layout_ocr_utils.py` |
| 領域処理 | `crop_region`, `calculate_coverage`, `should_fallback` | ~100行 | `layout_ocr_utils.py` |
| フォーマット | `format_ocr_result`, `select_ocr_engine` | ~80行 | `layout_ocr_utils.py` |

**推奨アクション**: ヘルパー関数を `layout_ocr_utils.py` に抽出

**違反関数**:
- `ocr_by_layout` (L354): 24 locals
- `run_layout_ocr` (L485): 28 locals, 60 statements

---

### 4. src/rover/ensemble.py (593行)

**シンボル構成**:
- Constants: 1 (`ENGINE_WEIGHTS`)
- Classes: 3 (`OCRLine`, `AlignedLine`, `ROVERResult`)
- Functions: 10

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| ライン処理 | `cluster_lines_*`, `align_lines_*`, `split_multiline_*` | ~200行 | `rover/line_processing.py` |
| 投票 | `vote_line_text`, `normalize_confidence` | ~100行 | `rover/voting.py` |
| マージ | `rover_merge` | ~100行 | 維持 |
| 実行 | `run_rover_*`, `main` | ~150行 | 維持 |

**推奨アクション**: ライン処理を `line_processing.py` に抽出

**違反関数**:
- `cluster_lines_by_y` (L246): 19 locals
- `align_lines_by_y` (L360): 19 locals
- `rover_merge` (L470): 18 locals

---

### 5. src/ocr_integrated.py (577行)

**シンボル構成**:
- Classes: 1 (`IntegratedResult`)
- Constants: 1 (`ENGINE_PRIORITY`)
- Functions: 9

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| 領域処理 | `filter_overlapping_*`, `group_text_*` | ~150行 | `ocr_integrated_utils.py` |
| 構造化 | `structure_text_*`, `extract_titles_*` | ~200行 | `ocr_integrated_utils.py` |
| 実行 | `run_integrated_*`, `main` | ~200行 | 維持 |

**推奨アクション**: ヘルパー関数を抽出

**違反関数**:
- `group_text_by_regions` (L102): 20 locals
- `run_integrated_ocr` (L344): 26 locals, 15 branches, 65 statements
- `run_integrated_ocr_batch` (L458): 26 locals

---

### 6. src/book_converter/transformer.py (566行)

**シンボル構成**:
- Functions: 20

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| ブック変換 | `transform_book*` | ~100行 | 維持 |
| 章・節変換 | `transform_chapter`, `transform_section` | ~100行 | 維持 |
| コンテンツ変換 | `transform_paragraph`, `transform_heading`, `transform_list`, `transform_figure*` | ~200行 | `transformer_content.py` |
| TOC変換 | `transform_toc_*`, `transform_table_of_contents` | ~80行 | 維持 |
| ユーティリティ | `normalize_heading_*`, `is_duplicate_*`, `apply_emphasis` | ~80行 | `transformer_utils.py` |

**推奨アクション**: コンテンツ変換とユーティリティを分離

---

### 7. src/ocr_yomitoku.py (535行)

**シンボル構成**:
- Variables: 2 (`_yomitoku_analyzer`, `detect_layout`)
- Classes: 1 (`YomitokuResult`)
- Functions: 11

**論理グループ分析**:

| グループ | 関数 | 推定行数 | 分割先 |
|----------|------|----------|--------|
| OCR実行 | `ocr_page_*`, `ocr_pages_*` | ~200行 | 維持 |
| 結果管理 | `save_*`, `load_*`, `reset_analyzer` | ~100行 | `yomitoku_io.py` |
| レイアウト | `paragraphs_to_layout`, `detect_layout_*`, `visualize_layout` | ~150行 | `yomitoku_layout.py` |

**推奨アクション**: I/Oとレイアウト処理を分離

**違反関数**:
- `ocr_page_yomitoku` (L105): 16 locals
- `ocr_page_yomitoku_full` (L182): 20 locals
- `visualize_layout` (L430): 23 locals

---

## 関数リファクタリング戦略

### too-many-locals 解消パターン

1. **データクラス化**: 関連変数をdataclassにグループ化
   ```python
   # Before: 20+ locals
   def process(data):
       x1, y1, x2, y2 = ...
       width, height = ...

   # After: dataclass使用
   @dataclass
   class BBox:
       x1: int; y1: int; x2: int; y2: int
       @property
       def width(self): return self.x2 - self.x1
   ```

2. **ヘルパー関数抽出**: 処理ブロックを関数に分離
   ```python
   # Before: 長い関数
   def main_func():
       # 前処理 (5 locals)
       # メイン処理 (10 locals)
       # 後処理 (5 locals)

   # After: 分離
   def preprocess(): ...
   def postprocess(): ...
   def main_func():
       data = preprocess()
       result = process(data)
       return postprocess(result)
   ```

### too-many-branches 解消パターン

1. **早期リターン**
   ```python
   # Before
   if condition:
       if another:
           process()

   # After
   if not condition:
       return
   if not another:
       return
   process()
   ```

2. **辞書ディスパッチ**
   ```python
   # Before
   if type == "a": do_a()
   elif type == "b": do_b()

   # After
   handlers = {"a": do_a, "b": do_b}
   handlers[type]()
   ```

---

## 決定事項

| 項目 | 決定 | 根拠 |
|------|------|------|
| parser.py分割方式 | パッケージ化 | 1700+行は単純分割では不十分 |
| page_grouper.py分割方式 | パッケージ化 | 1100+行は同様 |
| 中規模ファイル分割方式 | ヘルパー抽出 | 500-600行は関数抽出で十分 |
| 循環インポート対策 | 設計見直し優先 | spec clarification準拠 |
| 公開API維持方式 | `__init__.py`で再エクスポート | 後方互換性維持 |

---

## 代替案の検討

| 代替案 | 評価 | 採用/却下理由 |
|--------|------|--------------|
| pylint制限値を緩和 | ❌ 却下 | 品質基準を下げるのは本末転倒 |
| 一部ファイルをpylint除外 | ❌ 却下 | 一貫性喪失、技術的負債 |
| 段階的移行（deprecation期間） | ⚠️ 部分採用 | 公開APIのみ、内部は即時変更 |
| 全ファイル同時リファクタリング | ❌ 却下 | リスク高、検証困難 |
