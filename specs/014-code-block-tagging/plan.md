# Implementation Plan: コードブロックタグ付け機能

**Branch**: `014-code-block-tagging` | **Date**: 2026-02-21 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/014-code-block-tagging/spec.md`

## Summary

書籍ページ画像内のコードブロックを自動検出し、`<code readAloud="false">`タグでマークアップする機能を追加する。

**技術アプローチ**:
1. OpenCV枠線検出で矩形候補を抽出
2. Guesslang（TensorFlowベース）でコード/非コード判定
3. yomitoku完了後にlayout.jsonを更新（IoU>0でTEXT→CODE置換）
4. book_converterでCode要素をXML出力

## Technical Context

**Language/Version**: Python 3.13+ (Constitution準拠)
**Primary Dependencies**: OpenCV, Guesslang, TensorFlow (Guesslang依存)
**Storage**: ファイルベース（layout.json更新）
**Testing**: pytest (Constitution準拠)
**Target Platform**: Linux (開発環境)
**Project Type**: single (既存構造に追加)
**Performance Goals**: 既存処理の20%以上の性能低下なし (SC-004)
**Constraints**: コード検出精度≥90%、誤検出率≤5%
**Scale/Scope**: 1ページあたり数個のコードブロック

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | yomitoku後の独立ステップとして設計 |
| II. Test-First | ✅ PASS | TDD必須、pytest使用 |
| III. Ollama Integration | N/A | コード検出はOllama不使用（OpenCV+Guesslang） |
| IV. Immutability | ✅ PASS | Code, CodeRegionは frozen dataclass |
| V. Simplicity (YAGNI) | ✅ PASS | コード/非コード二値判定のみ（言語判定なし） |

**Technical Constraints**:
- Python 3.13+: ✅ 準拠
- 依存管理: ✅ requirements.txt + venv
- ビルド/テスト: ✅ Makefile
- 画像処理: ✅ OpenCV使用

**Gate Result**: ✅ PASS - 全項目クリア

## Project Structure

### Documentation (this feature)

```text
specs/014-code-block-tagging/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── layout/
│   ├── detector.py          # 既存: yomitokuレイアウト検出
│   ├── code_detector.py     # NEW: OpenCV枠線検出 + Guesslang判定
│   ├── reading_order.py     # 既存: 読み順序決定
│   └── figures.py           # 既存: 図表処理
├── book_converter/
│   ├── models.py            # MODIFY: Code dataclass追加
│   ├── parser/
│   │   └── code.py          # NEW: コード領域パーサー
│   └── xml_builder.py       # MODIFY: <code>要素出力
└── cli/
    └── detect_layout.py     # MODIFY: コード検出オプション追加

tests/
├── unit/
│   ├── layout/
│   │   └── test_code_detector.py  # NEW
│   └── book_converter/
│       └── parser/
│           └── test_code.py       # NEW
└── integration/
    └── test_code_pipeline.py      # NEW
```

**Structure Decision**: 既存の`src/layout/`内に`code_detector.py`を追加。レイアウト検出の拡張として自然な配置。

## Complexity Tracking

> No violations - complexity tracking not required.

## Implementation Phases

### Phase 1: Setup
- 依存追加（opencv-python, guesslang）
- テスト環境準備

### Phase 2: Core Detection (TDD)
- OpenCV枠線検出
- Guesslang判定
- layout.jsonマージ

### Phase 3: Data Model
- Code dataclass
- CodeRegion dataclass
- SectionElement拡張

### Phase 4: Parser Integration
- code.pyパーサー
- xml_builder拡張

### Phase 5: CLI Integration
- detect_layout.pyオプション追加

### Phase 6: Polish
- エッジケーステスト
- パフォーマンス検証
