# Implementation Plan: コードブロック視覚検出

**Branch**: `021-code-block-gray-detection` | **Date**: 2026-03-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/021-code-block-gray-detection/spec.md`

## Summary

yomitoku が TEXT/FIGURE として誤分類するコードブロックを、灰色背景検出（画像分析）とテキスト分析（記号比率 + 拡張キーワード）の2段階で CODE リージョンに再分類する。隣接する CODE 断片を結合し、Markdown コードフェンスで出力する。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: OpenCV (画像処理・灰色背景検出), Pillow (画像クロップ), PyYAML (設定)
**Storage**: ファイルベース（layout.json, config.yaml）
**Testing**: pytest (make test)
**Target Platform**: Linux
**Project Type**: single
**Performance Goals**: コード検出追加処理 < 1秒/ページ（yomitoku テキスト利用で追加 OCR 不要）
**Constraints**: yomitoku の既存テキスト出力のみ使用。追加 OCR エンジン起動なし
**Scale/Scope**: 1冊あたり数百ページ、ページあたり 0-20 リージョン

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| I. Pipeline-First | ✅ PASS | レイアウト検出ステップ内の後処理として実装。独立テスト可能 |
| II. Test-First | ✅ PASS | TDD で実装。pytest 使用 |
| III. Ollama Integration | N/A | OCR は yomitoku 既存テキスト使用。Ollama 不使用 |
| IV. Immutability | ✅ PASS | 新しいリージョン dict を生成。入力データ変更なし |
| V. Simplicity (YAGNI) | ✅ PASS | 要求された機能のみ実装。閾値は設定化するが過剰な抽象化なし |

## Project Structure

### Documentation (this feature)

```text
specs/021-code-block-gray-detection/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/
├── layout/
│   ├── __init__.py          # Export code_detector module
│   ├── detector.py          # paragraphs_to_layout() 変更: cv_img 引数追加 + CODE 判定統合
│   ├── code_detector.py     # 新規: 灰色背景検出 + テキスト分析 + 断片結合
│   └── reading_order.py     # 変更なし
├── layout_ocr.py            # 変更なし（CODE は既存ルーティングで処理される）
├── layout_ocr_utils.py      # format_ocr_result() に CODE 追加, select_ocr_engine() に CODE 追加
└── yomitoku_layout.py       # 変更なし（detector.py 経由で自動反映）

tests/
├── test_code_detector.py    # 新規: 灰色背景検出 + テキスト分析 + 断片結合テスト
└── test_layout_ocr.py       # 追加: CODE 向け format/engine テスト
```

**Structure Decision**: 既存の `src/layout/` パッケージに `code_detector.py` を新規追加。検出ロジックは `detector.py` の `paragraphs_to_layout()` で統合。

## Implementation Phases

### Phase 1: 灰色背景検出モジュール (US-1)

**目的**: TEXT リージョンの灰色背景を検出し CODE に再分類

**変更ファイル**:
| File | Change |
|------|--------|
| `src/layout/code_detector.py` | 新規: `detect_gray_background()` |
| `src/layout/detector.py` | `paragraphs_to_layout()` に `cv_img` パラメータ追加 + 灰色判定呼び出し |
| `src/layout/detector.py` | `detect_layout_yomitoku()` で `cv_img` を `paragraphs_to_layout()` に渡す |
| `src/layout/detector.py` | `visualize_layout()` に `layout_regions` パラメータ追加で CODE 色分け |
| `src/layout/__init__.py` | `code_detector` を export に追加 |
| `tests/test_code_detector.py` | 新規: 灰色背景検出テスト |

**詳細**:

1. `detect_gray_background(cv_img, bbox, threshold=0.7)` → `bool`
   - bbox で画像切り出し → HSV 変換 → 灰色画素比率計算
   - 灰色条件: 彩度(S) < 30 かつ 明度(V) 50-200
   - 入力バリデーション: None 画像、範囲外 bbox 対応

2. `paragraphs_to_layout()` の変更:
   - `cv_img=None` キーワード引数追加（後方互換）
   - TEXT リージョンで `cv_img` が提供された場合のみ灰色チェック
   - アスペクト比 > 8.0 の帯状リージョンは除外
   - 灰色判定 True → `type="CODE"`, `label="code"`

3. `detect_layout_yomitoku()` の変更:
   - `paragraphs_to_layout()` 呼び出し時に `cv_img=cv_img` を渡す
   - 出力サマリに `[CODE: N]` を追加

4. `visualize_layout()` の変更:
   - `layout_regions` 引数追加（layout.json のリージョン情報）
   - CODE リージョンを黄色(0, 255, 255)で描画

**テスト**:
- 灰色画像 → True, 白画像 → False, 黒画像 → False
- 閾値境界テスト（0.7 前後）
- アスペクト比フィルタテスト
- None 画像 / 範囲外 bbox → False
- `paragraphs_to_layout()` 統合テスト: cv_img ありで CODE 生成

---

### Phase 2: OCR パイプライン CODE 対応 (US-1 完了)

**目的**: CODE リージョンの OCR フォーマットとエンジン選択

**変更ファイル**:
| File | Change |
|------|--------|
| `src/layout_ocr_utils.py` | `format_ocr_result()` に CODE 追加: ` ```\n{text}\n``` ` |
| `src/layout_ocr_utils.py` | `select_ocr_engine()` に CODE 追加: → "yomitoku" |
| `tests/test_layout_ocr.py` | CODE 向け format/engine テスト追加 |

**詳細**:

1. `format_ocr_result("CODE", text)` → ` ```\n{text}\n``` `
2. `select_ocr_engine("CODE")` → `"yomitoku"`

**テスト**:
- `format_ocr_result("CODE", "class Foo {}")` → コードフェンス囲み
- `select_ocr_engine("CODE")` → `"yomitoku"`

---

### Phase 3: テキスト分析によるコード判定 (US-2, US-3)

**目的**: TEXT + FIGURE リージョンのテキストを分析し CODE に再分類

**変更ファイル**:
| File | Change |
|------|--------|
| `src/layout/code_detector.py` | `detect_code_by_text()` 追加: 記号比率 + 拡張キーワード判定 |
| `src/layout/code_detector.py` | `calc_symbol_ratio()` 追加 |
| `src/layout/code_detector.py` | `count_code_keywords()` 追加 |
| `src/layout/code_detector.py` | `EXTENDED_KEYWORDS` 定数定義 |
| `src/layout/detector.py` | `paragraphs_to_layout()` に FIGURE テキスト分析追加 |
| `src/layout/detector.py` | `paragraphs_to_layout()` に TEXT テキスト分析追加 |
| `tests/test_code_detector.py` | テキスト分析テスト追加 |

**詳細**:

1. `calc_symbol_ratio(text)` → `float`
   - 対象記号: `{ } ( ) ; = < > [ ] ! & | + - * / % # @ ^ ~ \`
   - 空文字列 → 0.0

2. `count_code_keywords(text)` → `int`
   - 拡張キーワードリスト（25言語対応）:
     ```
     Python: def, import, from, self., async, await, lambda, elif
     Go: func, package, defer, :=
     Rust: fn, let, mut, impl, pub, struct, match
     Ruby/Elixir: require, module, defmodule, rescue
     C/C++: #include, typedef, sizeof(, std::
     JS/TS: const, function, =>
     IaC/DevOps: resource ", FROM, WORKDIR, RUN, COPY, CMD [, EXPOSE,
                 apiVersion:, kind:, spec:, hosts:, tasks:
     SQL: SELECT, WHERE, INSERT, CREATE
     Shell: #!/bin/, echo, ${
     General: class, void, private, public, return, throw, new, static,
              interface, extends, implements, var, val
     ```
   - 大文字小文字区別なし（SQL キーワード等対応）

3. `detect_code_by_text(text, sym_threshold=0.08, kw_threshold=2)` → `bool`
   - `calc_symbol_ratio(text) > sym_threshold` OR `count_code_keywords(text) >= kw_threshold`

4. `paragraphs_to_layout()` の変更:
   - FIGURE: `figure.paragraphs` からテキスト取得 → `detect_code_by_text()` で判定
   - TEXT: パラグラフの `contents` テキスト → `detect_code_by_text()` で判定
   - TITLE (section_headings) はスキップ（判定対象外）
   - 灰色背景検出が先、テキスト分析が後（OR 条件で統合）

**テスト**:
- `calc_symbol_ratio("class Foo { }")` > 0.08
- `calc_symbol_ratio("日本語テキスト")` ≈ 0.0
- `count_code_keywords("class Foo extends Bar")` >= 2
- `count_code_keywords("今日は良い天気です")` == 0
- `detect_code_by_text()` の OR 条件テスト
- FIGURE → CODE 再分類テスト
- TEXT → CODE 再分類テスト
- TITLE スキップテスト
- 日本語本文 false positive なしテスト

---

### Phase 4: 断片結合 (US-4)

**目的**: 隣接する CODE パラグラフを1つの CODE リージョンに結合

**変更ファイル**:
| File | Change |
|------|--------|
| `src/layout/code_detector.py` | `merge_code_fragments()` 追加 |
| `src/layout/code_detector.py` | `is_code_fragment()` 追加 |
| `src/layout/detector.py` | `paragraphs_to_layout()` 末尾で `merge_code_fragments()` 呼び出し |
| `tests/test_code_detector.py` | 断片結合テスト追加 |

**詳細**:

1. `is_code_fragment(text)` → `bool`
   - 短いテキスト (< 20文字) で記号比率が高い or `}` / `{` / `3` (OCR 誤読) のみ

2. `merge_code_fragments(regions, gap_threshold=80)` → `list[dict]`
   - regions を y 座標でソート
   - 隣接する CODE/FRAG リージョンを垂直ギャップで結合
   - non-CODE が間に入ったら結合打ち切り
   - 結合後の bbox = 外接矩形
   - 新しいリージョンリストを返す（イミュータブル）

3. `paragraphs_to_layout()` の変更:
   - 全リージョン分類後に `merge_code_fragments()` を呼び出し

**テスト**:
- 隣接 CODE + CODE → 1つの CODE
- CODE + non-CODE + CODE → 2つの CODE
- CODE + FRAG + CODE → 1つの CODE
- ギャップ > 閾値 → 結合しない
- イミュータブル性テスト

---

### Phase 5: 設定外部化と統合テスト (US-5, FR-011)

**目的**: 閾値を config.yaml に外部化、可視化・出力の最終調整

**変更ファイル**:
| File | Change |
|------|--------|
| `config.yaml` | コード検出閾値セクション追加 |
| `src/layout/code_detector.py` | config.yaml からの閾値読み込み対応 |
| `src/layout/detector.py` | detect_layout_yomitoku() のサマリ出力に CODE 数表示 |
| `tests/test_code_detector.py` | 設定読み込みテスト追加 |

**設定項目**:
```yaml
# Code detection settings
code_detection:
  gray_background_threshold: 0.7
  gray_saturation_max: 30
  gray_value_min: 50
  gray_value_max: 200
  aspect_ratio_max: 8.0
  symbol_ratio_threshold: 0.08
  keyword_threshold: 2
  fragment_gap_threshold: 80
```

**テスト**:
- デフォルト値でのテスト
- カスタム閾値でのテスト
- 実画像検証（手動）

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| 閾値が書籍ごとに異なる | 検出精度低下 | config.yaml で外部設定化。チューニング可能 |
| FIGURE 内 paragraphs テキストが取得不可 | FIGURE → CODE 再分類不可 | yomitoku の figure.paragraphs フィールドの有無を事前確認 |
| `}` → `3` OCR 誤読パターン | 断片結合の精度低下 | `3` を `}` の候補として扱うフラグメント判定 |
| 日本語本文の false positive | 品質低下 | 記号比率 0.08 は日本語テキストでは到達しないことを検証済み |

## Dependency Graph

```
Phase 1 (灰色背景検出)
    ↓
Phase 2 (OCR CODE 対応)
    ↓
Phase 3 (テキスト分析) ← Phase 1, 2 に依存
    ↓
Phase 4 (断片結合) ← Phase 3 に依存
    ↓
Phase 5 (設定外部化) ← Phase 1-4 に依存
```
