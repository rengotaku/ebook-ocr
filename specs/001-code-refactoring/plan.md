# Implementation Plan: コードベースリファクタリング

**Branch**: `001-code-refactoring` | **Date**: 2026-02-04 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-code-refactoring/spec.md`

## Summary

モジュール間の不要な結合と重複コードを解消し、レガシーコードを除去し、テストスイートを導入する。
具体的には、`ocr_deepseek.py` → `ocr.py` の結合を共有ユーティリティ抽出で解消、`ocr.py` とレガシー依存を削除、
pytest ベースのテストを導入する。パイプラインの動作は変更しない（出力同一性を保証）。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Pillow, imagehash, doclayout-yolo, requests
**Storage**: ファイルシステム（画像ファイル + テキスト出力）
**Testing**: pytest
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single (CLIパイプラインツール)
**Performance Goals**: 既存パイプラインと同等の処理速度（リグレッションなし）
**Constraints**: Ollama API 依存（テスト時はモック化）
**Scale/Scope**: src/ 内 9ファイル / 1,167行 → リファクタリング後 ~950行

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | PASS | リファクタリングは既存パイプライン構造を維持。各ステップの独立性を損なわない |
| II. Test-First (NON-NEGOTIABLE) | PASS | TDD で実施: 共有ユーティリティのテスト作成 → FAIL → 実装 → PASS |
| III. Ollama Integration | PASS | Ollama 設定は変更なし。テスト時はモック化 |
| IV. Immutability & Side-Effect Isolation | PASS | 共有ユーティリティは純粋関数。I/O は境界に限定 |
| V. Simplicity (YAGNI) | PASS | 過剰な抽象化なし。共有ユーティリティは最小限の関数移動のみ |

全ゲート PASS。Phase 0 に進行可能。

## Project Structure

### Documentation (this feature)

```text
specs/001-code-refactoring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── __init__.py
├── pipeline.py          # メインオーケストレータ (169行)
├── video_hash.py        # SHA-256 ハッシュ (84行)
├── extract_frames.py    # FFmpeg フレーム抽出 (55行)
├── deduplicate.py       # 知覚ハッシュ重複除去 (70行)
├── detect_figures.py    # DocLayout-YOLO 検出 (140行)
├── ocr_deepseek.py      # DeepSeek-OCR (275行) ← 結合解消対象
├── describe_figures.py  # VLM 図表説明 (155行) ← 重複関数抽出対象
├── ocr.py               # [削除対象] レガシー Tesseract/EasyOCR (219行)
└── utils.py             # [新規] 共有ユーティリティ

tests/
├── conftest.py          # [新規] pytest fixtures
├── test_utils.py        # [新規] 共有ユーティリティのテスト
├── test_deduplicate.py  # [新規] 重複除去テスト
├── test_ocr_deepseek.py # [新規] DeepSeek-OCR テスト
└── test_describe_figures.py # [新規] 図表説明テスト

test/                    # [既存] テスト参照データ（変更なし）
├── student/
└── teacher/
```

**Structure Decision**: 既存の `src/` フラットモジュール構造を維持。`src/utils.py` を1ファイル追加するのみ。テストは `tests/` ディレクトリに pytest 規約で配置。

## Complexity Tracking

該当なし（Constitution Check に違反なし）。
