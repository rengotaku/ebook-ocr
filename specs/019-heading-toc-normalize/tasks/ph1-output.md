# Phase 1 Output: Setup

**Date**: 2026-03-02
**Status**: Completed

## Executed Tasks

- [x] T001 既存の TOC パース実装を確認: src/book_converter/parser/toc.py
- [x] T002 [P] 既存の見出しパース実装を確認: src/book_converter/parser/heading.py
- [x] T003 [P] 既存のモデル定義を確認: src/book_converter/models.py
- [x] T004 [P] 新規テストディレクトリを作成: tests/book_converter/parser/
- [x] T005 セットアップ結果を出力: specs/019-heading-toc-normalize/tasks/ph1-output.md

## Existing Code Analysis

### src/book_converter/parser/toc.py

**Structure**:
- `parse_toc_marker()`: `<!-- toc -->` / `<!-- /toc -->` マーカー検出
- `normalize_toc_line()`: TOC行の正規化（# や - プレフィックス除去、** 強調マーカー除去）
- `merge_toc_lines()`: 分割されたTOC行のマージ（Chapter/Episode/Column パターン）
- `split_toc_entries()`: 正規化済みTOCテキストを個別エントリに分割
- `parse_toc_lines()`: TOC行リストをTocEntryリストに変換
- `parse_toc_entry()`: 単一TOC行をTocEntryに変換（LLM分類対応）

**Required Updates**: なし（既存機能で十分）

**活用可能な既存機能**:
1. `normalize_toc_line()`: 見出し行の # プレフィックス除去に利用可能
2. `parse_toc_entry()`: TOCエントリの番号・タイトル抽出に利用可能

### src/book_converter/parser/heading.py

**Structure**:
- `parse_heading()`: Markdown見出し行（# - ###）のパース → `Heading` オブジェクト生成
- `parse_structure_heading()`: 構造化見出し（Chapter N, Section N.N, Subsection N.N.N）のパース
- `parse_heading_with_warning()`: レベル4以上の警告付きパース

**Required Updates**: なし（既存機能で十分）

**活用可能な既存機能**:
1. `parse_heading()`: 本文見出し抽出に直接利用可能

### src/book_converter/models.py

**Structure**:
- `TocEntry`: TOCエントリモデル（text, level, number, page）
- `Heading`: 見出しモデル（level, text, read_aloud）
- `HeadingAnalysis`: 見出し分析結果（text, level, count, levels, is_running_head）
- `MarkerType`: マーカー種別列挙型

**Required Updates**:
1. 新規列挙型追加: `MatchType` (EXACT, FUZZY, MISSING, EXCLUDED)
2. 新規列挙型追加: `NormalizationAction` (ADD_NUMBER, ADD_MARKER, FORMAT_ONLY, NONE)
3. 新規データクラス追加: `MatchResult` (toc_entry, body_heading, match_type, similarity, line_number)
4. 新規データクラス追加: `NormalizationRule` (original, normalized, line_number, action)
5. 新規データクラス追加: `ValidationReport` (toc_entry_count, body_heading_count, matched_count, match_rate, missing_entries, excluded_headings)

## Existing Test Analysis

- `tests/book_converter/test_parser.py`: 既存パーサーテスト（見出し、TOC含む）
- `tests/book_converter/test_models.py`: モデルテスト
- **新規作成**: `tests/book_converter/parser/` ディレクトリ作成済み
- **新規作成**: `tests/book_converter/parser/test_heading_normalizer.py` → Phase 2 で作成
- **新規作成**: `tests/book_converter/test_heading_matcher.py` → Phase 3 で作成
- **新規作成**: `tests/book_converter/test_normalization_rules.py` → Phase 3-4 で作成

**Required Fixtures**:
- `sample_book_md`: TOCと見出しを含むサンプル book.md コンテンツ
- `sample_toc_entries`: パース済み TocEntry リスト
- `sample_body_headings`: パース済み Heading リスト

## Newly Created Files

### tests/book_converter/parser/__init__.py (skeleton)

- 空ファイル（パッケージマーカー）

### src/book_converter/parser/heading_normalizer.py (to be created in Phase 2)

- `normalize_number_format()`: 番号フォーマットをドット区切りに統一
- `normalize_spaces()`: 番号周辺のスペースを除去
- `is_special_marker()`: 特殊マーカー（■、◆等）を検出
- `extract_headings()`: book.md から見出し行を抽出
- `classify_heading_patterns()`: 見出しを3カテゴリに分類

### src/book_converter/heading_matcher.py (to be created in Phase 3)

- `match_toc_to_body()`: TOCエントリと本文見出しをマッチング
- `find_similar_candidate()`: 類似候補を検索

### src/book_converter/normalization_rules.py (to be created in Phase 3-4)

- `generate_rules()`: マッチング結果から正規化ルールを生成
- `generate_sed_script()`: sed コマンドスクリプトを生成
- `preview_diff()`: 変更プレビューを生成
- `apply_rules()`: ルールを適用

### src/cli/normalize_headings.py (to be created in Phase 6)

- `report` サブコマンド: 見出しパターン分析レポート
- `normalize` サブコマンド: 正規化（--apply オプション）
- `validate` サブコマンド: TOC検証レポート

## Technical Decisions

1. **difflib.SequenceMatcher を使用**: 追加依存なし、日本語文字列対応、標準ライブラリ
2. **既存 TocEntry/Heading モデルは変更なし**: 新規モデルで拡張、後方互換性維持
3. **純粋関数優先**: 正規化ロジックは副作用なしの純粋関数として実装
4. **sed スクリプト出力**: POSIX 互換、GNU 拡張なし

## Handoff to Next Phase

Items to implement in Phase 2 (US1 - 見出しパターンの自動抽出):
- `normalize_number_format()`: `1-1-1` → `1.1.1`, `１．１` → `1.1` 等の正規化
- `normalize_spaces()`: `第 1 章` → `第1章`, `1. 1` → `1.1` 等の正規化
- `is_special_marker()`: `■xxx`, `◆xxx` 等の検出
- `extract_headings()`: `## ` で始まる行を抽出
- `classify_heading_patterns()`: 番号あり/なし/マーカーなしの3分類

Reusable existing code:
- `parse_heading()`: Heading オブジェクト生成に利用可能
- `normalize_toc_line()`: # プレフィックス除去に参考可能

Caveats:
- 既存の `normalize_toc_line()` は番号フォーマット正規化を行わない
- 新規に `heading_normalizer.py` を作成し、専用の正規化関数を実装する
