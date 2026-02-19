# Phase 2 出力: User Story 1 - ruffによるコード品質チェック (Priority: P1) MVP

**日時**: 2026-02-18
**フェーズ**: Phase 2
**ステータス**: 完了

## サマリー

| 項目 | 結果 |
|------|------|
| pyproject.toml | 新規作成完了 |
| ruff check | エラー0件（All checks passed!） |
| ruff format | 41ファイルフォーマット済 |
| テスト結果 | 1306 passed, 6 skipped |

## 作業内容

### T008: pyproject.toml作成

**ファイル**: `/data/projects/video-separater/pyproject.toml`

```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

設定内容:
- 1行の最大文字数: 120
- Pythonバージョン: 3.13
- 有効化ルール: E (error), F (pyflakes), I (isort), W (warning)

### T009: ruff check実行（違反確認）

初回実行結果: 59件のエラー検出

主な違反タイプ:
- I001: Import block is un-sorted or un-formatted（多数）
- F401: Imported but unused（複数箇所）
- F541: f-string without any placeholders
- E501: Line too long (>120)
- E402: Module level import not at top of file
- E741: Ambiguous variable name
- F821: Undefined name

### T010: ruff check --fix実行（自動修正）

自動修正結果: 50件修正、9件残存

残存エラー:
- E501 (2件): 長い行（cli.py, page_grouper.py）
- E402 (2件): ファイル途中のimport（parser.py, transformer.py）
- F841 (1件): 未使用変数（parser.py）
- E741 (2件): 曖昧な変数名 `l`（parser.py, ocr_ensemble.py）
- F821 (1件): 未定義名 `SYSTEM_PROMPT`（toc_classifier.py）

### T011: ruff format実行

フォーマット結果: 30ファイル再フォーマット、11ファイル変更なし

### T012: 手動修正（残り9件）

#### 1. E501: 長い行の修正（2件）

**src/book_converter/cli.py:233**
```python
# Before (138文字)
print(f"見出しレベル設定: L1={header_level_config.level1}, L2={header_level_config.level2}, L3={header_level_config.level3}")

# After (分割)
print(
    f"見出しレベル設定: L1={header_level_config.level1}, "
    f"L2={header_level_config.level2}, L3={header_level_config.level3}"
)
```

**src/book_converter/page_grouper.py:554**
```python
# Before (127文字)
print(f"  コンテンツタグ: heading={headings_after}, paragraph={paragraphs_count}, list={lists_count}, figure={figures_count}")

# After (分割)
print(
    f"  コンテンツタグ: heading={headings_after}, paragraph={paragraphs_count}, "
    f"list={lists_count}, figure={figures_count}"
)
```

#### 2. E402: ファイル途中のimport修正（2件）

**src/book_converter/parser.py:65**
- `import re` をファイル先頭（7行目）に移動
- 65行目の重複import削除

**src/book_converter/transformer.py:409**
- 後続のLegacy functionsセクションで使用するモデルをファイル先頭のimportに追加
- 409-415行目の重複import削除

追加されたimport:
```python
from src.book_converter.models import (
    # 既存
    Book,
    BookMetadata,
    Chapter,
    Figure,
    Heading,
    List,
    Paragraph,
    Section,
    TableOfContents,
    TocEntry,
    # 追加
    Content,
    Page,
    PageAnnouncement,
    PageMetadata,
    StructureContainer,
)
```

#### 3. F841: 未使用変数削除（1件）

**src/book_converter/parser.py:1247**
```python
# Before
description = "\n".join(description_lines) if description_lines else ""

# After
# (行削除 - descriptionは使用されていない)
```

#### 4. E741: 曖昧な変数名修正（2件）

**src/book_converter/parser.py:1361**
```python
# Before
for i, l in enumerate(lines[:5], start=1):
    print(f"  {i}: {l!r}", file=sys.stderr)

# After
for i, line_text in enumerate(lines[:5], start=1):
    print(f"  {i}: {line_text!r}", file=sys.stderr)
```

**src/ocr_ensemble.py:685**
```python
# Before
easyocr_langs = [l.strip() for l in args.easyocr_langs.split(",")]

# After
easyocr_langs = [lang.strip() for lang in args.easyocr_langs.split(",")]
```

#### 5. F821: 未定義名修正（1件）

**src/book_converter/toc_classifier.py**

問題: `classify_toc_entry_with_llm()` 関数が未定義の `SYSTEM_PROMPT` を参照

修正: SYSTEM_PROMPTを定義（61行目に追加）
```python
# System prompt for single TOC entry classification
SYSTEM_PROMPT = """You are a TOC (Table of Contents) entry classifier.

Classify the TOC entry level based on its number format:
- "chapter": Single number or "Chapter N" (e.g., "1", "Chapter 1", "第1章")
- "section": Two-part number (e.g., "2.1", "3.2")
- "subsection": Three+ part number (e.g., "2.1.1", "2.1.1.1")
- "other": No hierarchical number (Episode, Column, etc.)

Return ONLY a JSON object:
{"level": "section", "number": "2.1", "title": "SLOを理解するための4つの要素"}
"""
```

## 検証結果

### T013: ruff check検証

```
$ ruff check src/
All checks passed!
```

**結果**: ✅ エラー0件

### T014: ruff format検証

```
$ ruff format --check src/
41 files already formatted
```

**結果**: ✅ 全ファイルフォーマット済

### T015: テスト実行

```
$ make test
======================= 1306 passed, 6 skipped in 11.26s =======================
```

**結果**: ✅ 全テストパス（ベースライン1306件維持）

## 変更ファイル一覧

| ファイル | 変更種別 | 内容 |
|----------|----------|------|
| `pyproject.toml` | 新規作成 | ruff設定 |
| `src/book_converter/cli.py` | 修正 | E501修正（長い行分割） |
| `src/book_converter/page_grouper.py` | 修正 | E501修正（長い行分割） |
| `src/book_converter/parser.py` | 修正 | E402（import移動）、F841（未使用変数削除）、E741（変数名変更） |
| `src/book_converter/transformer.py` | 修正 | E402（import統合） |
| `src/book_converter/toc_classifier.py` | 修正 | F821（SYSTEM_PROMPT追加） |
| `src/ocr_ensemble.py` | 修正 | E741（変数名変更） |
| その他30ファイル | 自動フォーマット | ruff formatによる整形 |

## 次フェーズへの引き継ぎ

### Phase 3（ファイル分割）への準備完了

1. **コード品質基盤確立**: ruff check/format がエラー0件で実行可能
2. **テストスイート維持**: 1306件のテストが全てパス
3. **設定ファイル配置**: pyproject.toml がリポジトリルートに配置済み

### Phase 3で実施する内容

1. `src/ocr_ensemble.py` (699行) → 4モジュールに分割
2. `src/rover/engines.py` (613行) → 3モジュールに分割
3. 分割後も ruff check/format が通ることを確認
4. 全テストがパスすることを確認

### 注意事項

- **Phase 3終了後にPre-commit設定**: FR-010の実装順序制約に従い、ファイル分割完了後にpre-commit設定を追加（Phase 4）
- **ruff実行が必須**: 以降のすべてのコード変更後は `ruff check --fix && ruff format` を実行
- **import最適化済み**: ruff の I001 (isort) ルールにより、import文が自動整理されている

## 成果

### Success Criteria 達成状況

| SC | 内容 | 状態 |
|----|------|------|
| SC-001 | `ruff check src/` がエラー0件で完了する | ✅ 達成 |
| SC-002 | すべての `.py` ファイルが `ruff format` で変更なしの状態を維持する | ✅ 達成 |
| SC-005 | 既存のテストスイート（`pytest`）がすべてパスする | ✅ 達成 |

**ステータス**: Phase 2 完了 ✅
