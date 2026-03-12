# Phase 4 Output: US4 断片化コードブロックの結合

**Date**: 2026-03-13
**Status**: Completed
**User Story**: US4 - 断片化コードブロックの結合

## 実行タスク

- [x] T063 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph4-test.md`
- [x] T064 `is_code_fragment(text)` を実装: 短いテキストの断片判定 in `src/layout/code_detector.py`
- [x] T065 `merge_code_fragments(regions, gap_threshold)` を実装: 隣接 CODE/FRAG の結合 + 外接矩形計算 in `src/layout/code_detector.py`
- [x] T066 `paragraphs_to_layout()` 末尾で `merge_code_fragments()` を呼び出し in `src/layout/detector.py`
- [x] T067 `make test` で PASS を確認 (GREEN)
- [x] T068 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T069 `make lint` で lint エラーなしを確認
- [x] T070 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph4-output.md`

## 変更ファイル

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `src/layout/code_detector.py` | 変更 | `is_code_fragment()` と `merge_code_fragments()` を追加 |
| `src/layout/detector.py` | 変更 | `paragraphs_to_layout()` に `text` フィールド追加と `merge_code_fragments()` 呼び出しを追加 |
| `tests/test_code_detector.py` | 変更 | ruff format による自動整形（フォーマット統一） |

## テスト結果

```
========= 1676 passed, 2 skipped, 131 deselected, 6 warnings in 35.52s =========
```

- Phase 4 RED テスト 33 件がすべて GREEN に転換
- Phase 2・3 テスト含む全テストのリグレッションなし
- lint: `make lint` パス（ruff check + ruff format + pylint --exit-zero）

**Coverage**: 計測対象外（make test のみ実行）

## 実装の詳細

### `is_code_fragment(text)` アルゴリズム

- None・空文字列・空白のみ → False
- 20文字以上（strip後） → False
- OCR誤読パターン（`"3"` → `}` の誤読）→ True
- `calc_symbol_ratio(stripped) > 0.5`（コード記号が半数超） → True
- それ以外 → False

### `merge_code_fragments(regions, gap_threshold=80)` アルゴリズム

- 入力が空 → 空リスト返却
- `bbox[1]`（y上端）でソート
- 各リージョンを走査:
  - マージ不可（non-CODE かつ non-FRAG）→ そのままコピーして出力
  - マージ可能（CODE または is_code_fragment(text)=True）→ マージグループを蓄積
    - 次のリージョンもマージ可能かつ gap < gap_threshold → グループに追加
    - そうでなければ → グループを1つのCODEリージョンに結合して出力
- 結合bbox = 外接矩形 [min(x1), min(y1), max(x2), max(y2)]
- 結合後のtype = "CODE"、label = "code"
- イミュータブル: 入力リスト・入力dictを変更しない

### `paragraphs_to_layout()` の変更

- 段落リージョンに `"text": p.contents` フィールドを追加（`merge_code_fragments` が `text` フィールドを参照するため）
- FIGUREリージョンに `"text": ""` フィールドを追加
- 全リージョン構築後、`merge_code_fragments(regions)` を呼び出して返却

### ギャップ閾値の境界動作

gap == gap_threshold のケースは厳密な less-than (`<`) で判定。つまり gap == 80 の場合は結合しない。

## 発見した課題

なし（Phase 3 で確立した実装パターンをそのまま踏襲）

## 次フェーズへの引き継ぎ

Phase 5（US5 - 可視化・出力・設定外部化）で実装するもの:

- **確立したインターフェース**:
  - `src/layout/code_detector.py`: `is_code_fragment()`、`merge_code_fragments()` 完成
  - `paragraphs_to_layout()`: 末尾で `merge_code_fragments()` を呼び出し、CODE リージョンが結合済みで返される
  - リージョン dict に `"text"` フィールドが追加済み（merge 処理で使用）

- **Phase 5 で追加する機能**:
  - `visualize_layout()`: CODE リージョンを黄色で描画
  - `detect_layout_yomitoku()`: stdout に `[CODE: N]` サマリ出力
  - `config.yaml` の `code_detection` セクションから閾値を読み込む設定外部化

- **注意事項**:
  - `merge_code_fragments()` の結果リージョンには `"text"` フィールドが存在しない（マージ後は省略）。Phase 5 のテストでこのフィールドが必要な場合は対応要
  - 既存テスト（T013 等）で `paragraphs_to_layout()` の出力に `"text"` フィールドが含まれるようになったが、テストは `type` と `label` のみ検証のため問題なし
