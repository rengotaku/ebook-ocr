# Phase 3 Output: page_grouper.py パッケージ化

**Date**: 2026-02-19
**Branch**: `012-fix-pylint-errors`
**Status**: COMPLETE

## 実行サマリ

| Task | Description | Status |
|------|-------------|--------|
| T019 | ph1-output.md読込 | ✅ |
| T020 | ph2-output.md読込 | ✅ |
| T021 | page_grouper/ ディレクトリ作成 | ✅ |
| T022 | models.py 作成 | ✅ |
| T023 | section.py 作成 | ✅ |
| T024 | toc.py 作成 | ✅ |
| T025 | assignment.py 作成 | ✅ |
| T026 | hierarchy.py 作成 | ✅ |
| T027 | xml.py 作成 | ✅ |
| T028 | __init__.py 作成 | ✅ |
| T029 | 元page_grouper.py削除 | ✅ |
| T030 | pytest確認 | ✅ (94/94) |
| T031 | pylint確認 | ✅ (9.94/10) |
| T032 | ph3-output.md生成 | ✅ |

## 成果物

### 作成されたファイル

```
src/book_converter/page_grouper/
├── __init__.py         # 53行: 公開API再エクスポート
├── models.py           # 57行: FlattenStats, SectionNumber, TOCEntry
├── section.py          # 234行: セクション番号抽出・解析
├── toc.py              # 78行: TOC解析・ページ数検証
├── assignment.py       # 289行: ページ割当処理
├── hierarchy.py        # 439行: 階層構造構築
└── xml.py              # 106行: XML変換・シリアライズ
```

**Total**: 1256行（元: 1148行）

注: 分割によりimport文とdocstringが増加したため、総行数は微増。これは正常。

### 削除されたファイル

- `src/book_converter/page_grouper.py` (1148行)

## Pylint検証結果

### Before (元 page_grouper.py)
```
C0302: Too many lines in module (1148/500)
+ 1x too-many-locals
+ 1x too-many-branches
+ 1x too-many-statements
```

### After (page_grouper/ パッケージ)
```
Rating: 9.94/10

残存違反:
- R0912 (too-many-branches): 1関数
  - hierarchy.py::_add_sections_to_chapter (17 branches)

- R0914 (too-many-locals): 1関数
  - assignment.py::group_pages_by_toc (31 locals)

- R0915 (too-many-statements): 1関数
  - assignment.py::group_pages_by_toc (55 statements)
```

**改善率**:
- ファイル行数: 1148行 → 最大439行 (62%削減)
- too-many-lines違反: 1ファイル → 0ファイル ✅
- 複雑度違反: 3箇所 → 3箇所（関数レベルの違反は残存）

## Pytest検証結果

```
94 passed in 0.15s
```

全テストパス。後方互換性完全維持。

## モジュール設計

### 依存関係

```
models.py (依存なし)
    ↑
section.py ← toc.py
    ↑
assignment.py → hierarchy.py
    ↑
xml.py
    ↑
__init__.py (全てを再エクスポート)
```

**循環インポート**: なし

### 責務分担

| モジュール | 責務 | 行数 |
|-----------|------|------|
| models.py | データクラス定義 | 57 |
| section.py | セクション番号抽出・正規化 | 234 |
| toc.py | TOC解析・検証 | 78 |
| assignment.py | ページ割当・グループ化 | 289 |
| hierarchy.py | 階層構造構築・フラット化 | 439 |
| xml.py | XML変換・シリアライズ | 106 |

## 後方互換性

`__init__.py` で全関数を再エクスポートしているため、既存コードは変更不要:

```python
# Before
from src.book_converter.page_grouper import group_pages_by_toc

# After (同じ!)
from src.book_converter.page_grouper import group_pages_by_toc
```

## 次フェーズへの引き継ぎ

### Phase 4での対応が必要な項目

1. **assignment.py の関数リファクタリング** (289行)
   - `group_pages_by_toc` が複雑すぎる (31 locals, 55 statements)
   - フラット化処理をヘルパー関数に分離すべき

2. **hierarchy.py の関数リファクタリング** (439行)
   - `_add_sections_to_chapter` が複雑すぎる (17 branches)
   - 条件分岐を早期リターンで整理すべき

### 推奨される追加改善

**assignment.py**: `group_pages_by_toc` の分解案:
- `_create_book_structure`: メタデータ・TOC追加
- `_classify_pages`: フロントマター・コンテンツページ分類
- `_process_front_matter`: フロントマター処理
- `_process_content_pages`: コンテンツページ処理
- `_print_statistics`: 統計出力

**hierarchy.py**: `_add_sections_to_chapter` の改善案:
- 早期リターンで深いネストを削減
- 処理段階を明確に分離（章ページ、セクション、サブセクション）

## 問題点と解決策

### 問題1: 3つの関数が複雑度違反

**原因**:
- `group_pages_by_toc` が統計出力を含む多機能関数
- `_add_sections_to_chapter` が複数レベルの構造を1関数で処理

**解決策**: Phase 5で関数リファクタリング

### 問題2: assignment.pyとhierarchy.pyの相互依存

**現状**:
- assignment.py が hierarchy の `_flatten_pages_in_element`, `_build_hierarchical_structure` を使用
- hierarchy.py が assignment の関数は使用しない（一方向依存）

**結論**: 循環インポートなし。設計上問題なし。

## 備考

- WF-001に従い、作業中は `git commit --no-verify` 使用可
- ruff によるコード整形済み
- 循環インポート問題なし
- 全94テストパス（100%）
- pylint rating: 9.94/10（元: 9.89/10）
