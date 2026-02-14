# Implementation Plan: ROVER OCR再設計

**Branch**: `008-rover-redesign` | **Date**: 2026-02-14 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-rover-redesign/spec.md`

## Summary

真のROVER（Recognizer Output Voting Error Reduction）アルゴリズムの実装。文字レベルでのアライメント（difflib.SequenceMatcher）と信頼度重み付き多数決投票を行う。参加エンジンはyomitoku（主）+ PaddleOCR + EasyOCR（Tesseract除外）。信頼度は投票の重みとして使用し、閾値0.5以下はゴミとして除外。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: yomitoku>=0.10.0, paddleocr>=2.7.0, easyocr>=1.7.0, opencv-python (CLAHE), difflib (標準ライブラリ)
**Storage**: ファイルベース（raw/{engine}/, rover/）
**Testing**: pytest + pytest-cov (カバレッジ目標 ≥80%)
**Target Platform**: Linux/macOS (CPU/CUDA対応)
**Project Type**: single
**Performance Goals**: 処理時間が単一エンジン使用時の4倍以下
**Constraints**: CPU環境でも実行可能、メモリ効率を考慮
**Scale/Scope**: 1冊分のページ画像（100〜500ページ）を処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | ROVERは既存パイプラインの一部として動作、入力:画像、出力:テキスト |
| II. Test-First (NON-NEGOTIABLE) | ✅ PASS | TDDで実装、pytest使用、カバレッジ≥80%目標 |
| III. Ollama Integration | N/A | OCRエンジン直接利用、Ollamaは関係なし |
| IV. Immutability & Side-Effect Isolation | ✅ PASS | 純粋関数中心、ファイルI/Oは境界のみ |
| V. Simplicity (YAGNI) | ✅ PASS | 仕様に記載された機能のみ実装 |

**Technical Constraints Check**:
- ✅ Python 3.13+
- ✅ pytest使用
- ✅ Makefile対応（既存`rover-ocr`ターゲット更新）
- ✅ 画像処理: Pillow, OpenCV

## Project Structure

### Documentation (this feature)

```text
specs/008-rover-redesign/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── api.md           # Internal API contracts
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ocr_engines.py       # [UPDATE] yomitoku: words併用、EasyOCR: CLAHE前処理
├── ocr_rover.py         # [MAJOR REWRITE] 真のROVER: 文字レベル投票
├── ocr_preprocess.py    # [NEW] CLAHE前処理モジュール
├── ocr_alignment.py     # [NEW] 文字レベルアライメント
└── ocr_output.py        # [UPDATE] raw/rover出力構造

tests/
├── test_ocr_rover.py    # [NEW] ROVERユニットテスト
├── test_ocr_alignment.py # [NEW] アライメントテスト
├── test_ocr_preprocess.py # [NEW] 前処理テスト
└── conftest.py          # [UPDATE] 新しいfixtures
```

**Structure Decision**: 単一プロジェクト構造を維持。既存の`src/`と`tests/`を拡張。文字レベルアライメントは新規モジュール `ocr_alignment.py` に分離。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |

## Key Algorithm: True ROVER

### 処理フロー

```
[Image Input]
     │
     ▼
[OCR Processing] ─────────────────────┐
     │                                │  並列実行可能
     ├── yomitoku → EngineResult      │
     ├── paddleocr → EngineResult     │
     └── easyocr (CLAHE) → EngineResult
                                      │
     ▼◄────────────────────────────────┘
[Garbage Filter]
     │  confidence < 0.5 を除外
     │
     ▼
[Line Clustering]
     │  各エンジンの items を y座標でグループ化
     │
     ▼
[Line Alignment]
     │  y座標が近い行を cross-engine でマッチ
     │
     ▼
[Character-Level Alignment]  ← NEW
     │  difflib.SequenceMatcher で文字アライメント
     │
     ▼
[Weighted Voting]  ← NEW
     │  各位置で信頼度重み付き多数決
     │  weight = engine_weight * confidence
     │
     ▼
[ROVERResult]
```

### 信頼度重み付き投票

```python
# 各文字位置での投票
for position in aligned_positions:
    candidates = {engine: char for engine, char in ...}

    votes = {}
    for engine, char in candidates.items():
        weight = ENGINE_WEIGHTS[engine] * confidences[engine]
        votes[char] = votes.get(char, 0) + weight

    result_char = max(votes, key=votes.get)
```

### エンジン重み

| エンジン | 重み | 理由 |
|----------|------|------|
| yomitoku | 1.5 | 日本語OCRに最適化、最高品質 |
| PaddleOCR | 1.2 | 高精度、安定性 |
| EasyOCR | 1.0 | ベースライン |

## Phase Overview

### Phase 0: Research ✅
- yomitoku `paragraphs` + `words` 併用パターン
- difflib.SequenceMatcher の最適パラメータ
- CLAHE前処理パラメータ

### Phase 1: Design ✅
- データモデル設計（TextWithBox, AlignedPosition追加）
- 内部APIコントラクト
- クイックスタートガイド

### Phase 2: Tasks (speckit.tasks)
- TDDによるタスク分解
- 依存関係の明確化
