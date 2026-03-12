# Phase 3 Output: US2 + US3 テキスト分析によるコード検出

**Date**: 2026-03-13
**Status**: Completed
**User Story**: US2 - FIGURE 誤検出コードの救済, US3 - TEXT リージョン内コードの検出

## 実行タスク

- [x] T042 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph3-test.md`
- [x] T043 `EXTENDED_KEYWORDS` 定数を定義（25言語対応キーワードリスト） in `src/layout/code_detector.py`
- [x] T044 `calc_symbol_ratio(text)` を実装: 記号文字の比率を計算 in `src/layout/code_detector.py`
- [x] T045 `count_code_keywords(text)` を実装: 拡張キーワードの出現数をカウント in `src/layout/code_detector.py`
- [x] T046 `detect_code_by_text(text, sym_threshold, kw_threshold)` を実装: OR 条件判定 in `src/layout/code_detector.py`
- [x] T047 `paragraphs_to_layout()` に FIGURE テキスト分析を追加 in `src/layout/detector.py`
- [x] T048 `paragraphs_to_layout()` に TEXT テキスト分析を追加（TITLE はスキップ） in `src/layout/detector.py`
- [x] T049 `make test` で PASS を確認 (GREEN)
- [x] T050 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T051 `make lint` で lint エラーなしを確認
- [x] T052 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph3-output.md`

## 変更ファイル

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `src/layout/code_detector.py` | 変更 | `EXTENDED_KEYWORDS` 定数（25言語対応）を追加。`calc_symbol_ratio()`、`count_code_keywords()`、`detect_code_by_text()` を実装 |
| `src/layout/detector.py` | 変更 | `paragraphs_to_layout()` に TEXT テキスト分析（TITLE スキップ）と FIGURE テキスト分析（figure.paragraphs 走査）を追加 |
| `tests/test_code_detector.py` | 変更 | ruff format による自動整形（Phase 3 RED テスト作成時のスタイル修正） |

## テスト結果

```
========= 1643 passed, 2 skipped, 131 deselected, 6 warnings in 27.87s =========
```

- Phase 3 RED テスト 41 件がすべて GREEN に転換
- Phase 2 テスト含む全テストのリグレッションなし
- lint: `make lint` パス（ruff check + ruff format + pylint --exit-zero）

**Coverage**: 計測対象外（make test のみ実行、80% 目標は別途確認）

## 実装の詳細

### `EXTENDED_KEYWORDS` 定数

25言語以上に対応したキーワードリスト（合計65項目）:
- Python: `def `, `import `, `from `, `self.`, `async `, `await `, `lambda `, `elif `
- Go: `func `, `package `, `defer `, `:=`
- Rust: `fn `, `let `, `mut `, `impl `, `pub `, `struct `, `match `
- Ruby/Elixir: `require `, `module `, `defmodule `, `rescue `
- C/C++: `#include`, `typedef `, `sizeof(`, `std::`
- JS/TS: `const `, `function `, `=>`
- IaC/DevOps: `resource "`, `FROM `, `WORKDIR `, `RUN `, `COPY `, `CMD [`, `EXPOSE `, `apiVersion:`, `kind:`, `spec:`, `hosts:`, `tasks:`
- SQL: `SELECT `, `WHERE `, `INSERT `, `CREATE `
- Shell: `#!/bin/`, `echo `, `${`
- General: `class `, `void `, `private `, `public `, `return `, `throw `, `new `, `static `, `interface `, `extends `, `implements `, `var `, `val `

### `calc_symbol_ratio(text)` アルゴリズム

- 対象記号: `{}();=<>[]!&|+-*/%#@^~\` の frozenset
- 日本語句読点（。、「」等）は含まない
- 空文字列 → 0.0
- 総文字数に対する記号文字数の比率を返す

### `count_code_keywords(text)` アルゴリズム

- テキスト全体を小文字化してキーワードを大文字小文字無視でマッチ
- `str.count()` でキーワードごとの出現数を集計（重複あり）
- 空文字列 → 0

### `detect_code_by_text(text)` アルゴリズム

- None または空文字列 → False
- `calc_symbol_ratio(text) > sym_threshold`（デフォルト 0.08）→ True（OR 条件第1辺）
- `count_code_keywords(text) >= kw_threshold`（デフォルト 2）→ True（OR 条件第2辺）
- 両方不成立 → False

### `paragraphs_to_layout()` の変更

- TEXT 処理: 灰色背景検出の後、TEXT のままであれば `detect_code_by_text(p.contents)` を実行
  - True の場合 → `region_type = "CODE"`
  - TITLE（section_headings）はこのブロックに到達しないため自動スキップ
- FIGURE 処理: `hasattr(f, "paragraphs")` でガードし、`f.paragraphs` を走査
  - いずれか1つのパラグラフが `detect_code_by_text()` で True → `figure_type = "CODE"`, `figure_label = "code"` に変更
  - break で最初の検出後に中断（効率化）
- イミュータブル: 元の figure/paragraph オブジェクトは変更せず、新しい dict を生成

## 発見した課題

1. **test_code_detector.py の ruff format 問題**: Phase 3 RED テスト作成時にフォーマットが統一されていなかった。`ruff format` による自動整形で対応（テストロジックへの影響なし）

## 次フェーズへの引き継ぎ

Phase 4（US4 断片化コードブロックの結合）で実装するもの:

- **確立したインターフェース**:
  - `src/layout/code_detector.py`: テキスト分析モジュール完成。Phase 4 の断片結合関数（`is_code_fragment()`、`merge_code_fragments()`）をここに追加
  - `paragraphs_to_layout()`: 灰色検出 + テキスト分析の OR 条件統合済み。Phase 4 では末尾で `merge_code_fragments()` を呼び出す
  - CODE リージョンの `type="CODE"`, `label="code"` フォーマット確定

- **Phase 4 で追加する関数**:
  - `is_code_fragment(text)`: 短いテキストの断片判定（`}` / `{` / `3` OCR 誤読等）
  - `merge_code_fragments(regions, gap_threshold=80)`: 隣接 CODE/FRAG の bbox 結合

- **注意事項**:
  - `merge_code_fragments()` はイミュータブルに実装（入力リストを変更しない）
  - `}` → `3` の OCR 誤読パターンを `is_code_fragment()` で考慮
  - 結合後の bbox は外接矩形として計算
