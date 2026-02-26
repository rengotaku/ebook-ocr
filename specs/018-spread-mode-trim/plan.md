# Implementation Plan: Spread モード明示指定と Trim 制御の拡張

**Branch**: `018-spread-mode-trim` | **Date**: 2026-02-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-spread-mode-trim/spec.md`

## Summary

画像の見開き/単ページ判定を明示的なモード指定に変更し、2段階のトリミング制御（global-trim + split-trim）を追加する。また、パイプラインへの統合と2段階プレビュー機能を実装する。

**主要な変更点**:
1. `--mode` オプション追加（single/spread、デフォルト: single）
2. `--global-trim-*` オプション追加（分割前の上下左右トリミング）
3. 既存の `--left-trim` / `--right-trim` は分割後の外側エッジトリミングとして維持
4. `make preview-extract` / `make preview-trim` の2段階プレビュー
5. `make run` への split-spreads ステップ統合

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: Pillow (画像処理), PyYAML (設定読み込み)
**Storage**: ファイルシステム（PNG画像、YAML設定）
**Testing**: pytest
**Target Platform**: Linux (CLI)
**Project Type**: single
**Performance Goals**: バッチ処理、個別画像処理は1秒以内
**Constraints**: メモリ効率的な画像処理（大きな画像も扱う）
**Scale/Scope**: 数百〜数千ページの書籍画像

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Pipeline-First** | ✅ PASS | split-spreads は独立したパイプラインステップ |
| **II. Test-First** | ✅ PASS | pytest でテスト実装（TDD） |
| **III. Ollama Integration** | N/A | OCR/VLM は使用しない |
| **IV. Immutability** | ✅ PASS | 画像処理は新規ファイル生成、入力ファイルは変更しない |
| **V. Simplicity (YAGNI)** | ✅ PASS | 既存コード拡張、過度な抽象化なし |

**Technical Constraints Check**:
- Python 3.13+ ✅
- 依存管理: requirements.txt + venv ✅
- ビルド/テスト: Makefile ✅
- 画像処理: Pillow ✅

## Project Structure

### Documentation (this feature)

```text
specs/018-spread-mode-trim/
├── spec.md              # 仕様書（作成済み）
├── plan.md              # 本ファイル
├── research.md          # リサーチ結果
├── data-model.md        # データモデル
└── tasks.md             # タスクリスト（/speckit.tasks で生成）
```

### Source Code (repository root)

```text
src/
├── preprocessing/
│   └── split_spread.py  # 主要変更対象
├── cli/
│   └── split_spreads.py # CLI ラッパー（変更対象）
└── ...

tests/
├── preprocessing/
│   └── test_split_spread.py  # テスト追加
└── ...

Makefile                 # ターゲット追加
config.yaml              # 設定項目追加
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。`src/preprocessing/split_spread.py` を中心に拡張。

## Implementation Phases

### Phase 1: Spread モード明示指定 (P1)

**目標**: `--mode` オプションで single/spread を明示的に指定可能にする

**変更ファイル**:
- `src/preprocessing/split_spread.py` - モード引数追加、`is_spread_image` 関数を条件分岐に変更
- `src/cli/split_spreads.py` - `--mode` CLI引数追加
- `config.yaml` - `spread_mode` 設定追加
- `Makefile` - `SPREAD_MODE` 変数追加

**テスト**:
- モード指定時の動作確認（single→分割なし、spread→常に分割）
- 環境変数からの読み込み
- CLI引数の優先度

### Phase 2: Global Trim 追加 (P2)

**目標**: 分割前に全体画像に対して上下左右のトリミングを適用

**変更ファイル**:
- `src/preprocessing/split_spread.py` - `apply_global_trim()` 関数追加
- `src/cli/split_spreads.py` - `--global-trim-*` CLI引数追加
- `config.yaml` - `global_trim` 設定追加

**テスト**:
- global-trim の適用確認
- global-trim → split-trim の順序確認
- 単ページモードでの global-trim 適用

### Phase 3: 2段階プレビュー (P3)

**目標**: フレーム抽出と trim プレビューを分離

**変更ファイル**:
- `Makefile` - `preview-extract`, `preview-trim` ターゲット追加
- `src/cli/split_spreads.py` - プレビューモード対応

**テスト**:
- preview-extract でフレーム生成
- preview-trim で trim 適用（再抽出なし）
- 繰り返し実行時の動作

### Phase 4: パイプライン統合 (P3)

**目標**: `make run` に split-spreads ステップを統合

**変更ファイル**:
- `Makefile` - `run` ターゲットに split-spreads 追加

**テスト**:
- フルパイプライン実行
- 従来の個別コマンドとの結果一致

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| 既存動作の破壊 | Low | High | デフォルト値を現行動作に合わせる |
| 画像処理のメモリ使用量 | Low | Medium | 画像は1枚ずつ処理、即座にクローズ |

## Dependencies

- 既存の `src/preprocessing/split_spread.py` の理解
- 既存の `config.yaml` 設定項目の理解
- Makefile のパイプラインフロー理解
