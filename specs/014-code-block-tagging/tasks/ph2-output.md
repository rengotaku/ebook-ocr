# Phase 2 Output: コード検出コア機能 (GREEN)

**Date**: 2026-02-21
**Status**: Complete
**Phase**: Phase 2 - User Story 1 - コード検出コア機能

## 作業サマリー

Phase 2では、コード検出のコア機能を実装し、全13件の新規テストがPASSしました。

### 実装内容

1. **CodeRegion dataclass** - レイアウト検出結果のコード領域を表現
2. **CodeDetectionResult dataclass** - コード検出結果（1画像分）を表現
3. **is_code() 関数** - テキストがコードかどうかを判定
4. **detect_code_regions() 関数** - layout.jsonのTEXT領域を走査してCODE再分類

### 完了タスク

| タスク | 説明 | ステータス |
|--------|------|-----------|
| T013 | REDテスト読み込み | ✅ Complete |
| T014 | CodeRegion dataclass実装 | ✅ Complete |
| T015 | CodeDetectionResult dataclass実装 | ✅ Complete |
| T016 | is_code() 関数実装 | ✅ Complete |
| T017 | detect_code_regions() 関数実装 | ✅ Complete |
| T018 | make test PASS確認 | ✅ Complete |
| T019 | リグレッション確認 | ✅ Complete |

## 変更ファイル

### 新規作成

1. **src/layout/code_detector.py** (145行)
   - `CodeRegion` frozen dataclass
   - `CodeDetectionResult` frozen dataclass
   - `is_code(text, threshold)` - コード判定関数
   - `_is_code_heuristic(text, threshold)` - Heuristic fallback (Python 3.13)
   - `detect_code_regions(layout, threshold)` - TEXT→CODE再分類

### 変更

1. **requirements.txt**
   - コメント追加: opencv-python (transitive dependency)
   - コメント追加: guesslang (Python 3.13非対応)

2. **specs/014-code-block-tagging/tasks.md**
   - T013-T019 を [X] にマーク

## テスト結果

### 新規テスト（13件全てPASS）

**tests/unit/layout/test_code_detector.py**:

| テストクラス | テスト数 | 結果 |
|-------------|---------|------|
| TestIsCode | 4 | ✅ PASS |
| TestCodeRegion | 4 | ✅ PASS |
| TestDetectCodeInLayout | 5 | ✅ PASS |

#### TestIsCode (4テスト)

- `test_is_code_with_python_code` - Pythonコードがコード判定される
- `test_is_code_with_java_code` - Javaコードがコード判定される
- `test_is_code_with_japanese_text` - 日本語テキストが非コード判定される
- `test_is_code_with_empty_string` - 空文字列が非コード判定される

#### TestCodeRegion (4テスト)

- `test_code_region_creation` - CodeRegionの生成
- `test_code_region_default_ocr_text` - デフォルト値 (空文字列)
- `test_code_region_immutability` - frozen dataclassの不変性
- `test_code_region_non_code` - is_code=Falseの領域表現

#### TestDetectCodeInLayout (5テスト)

- `test_detect_code_in_layout` - TEXT→CODE再分類
- `test_detect_code_preserves_non_text_regions` - FIGURE/TITLE維持
- `test_detect_code_with_threshold` - 閾値による判定制御
- `test_detect_code_returns_new_layout` - 元データの不変性
- `test_detect_code_empty_regions` - 空regionsの処理

### 既存テスト

- **1306 tests PASS** (リグレッションなし)
- **6 tests SKIPPED**
- **0 tests FAIL**

## 実装上の問題と対応

### 問題1: Guesslang Python 3.13非対応

**現象**:
- guesslang==2.2.1 は tensorflow==2.5.0 に依存
- TensorFlow 2.5.0 は Python 3.13 に非対応 (最大3.9)
- TensorFlow 2.20.0 (Python 3.13対応) は `tensorflow.estimator` モジュールを削除済み

**対応**:
- Heuristic fallback実装 (`_is_code_heuristic()`)
- パターンベースのコード検出:
  - プログラミングキーワード (def, class, import, function, etc.)
  - 演算子・記号 (`{}()[];`, `=`, `==`, etc.)
  - メソッド呼び出しパターン (`\w+\(\)`)
  - インデントパターン (4+スペース、タブ)
  - 日本語比率チェック (非ASCII文字が30%超の場合は確信度を低下)

**精度**:
- テストケースでは十分な精度 (Pythonコード、Javaコード、日本語を正しく判定)
- 本番環境ではGuesslangを推奨 (Python 3.12以下で使用)

### 問題2: opencv-python 依存関係

**現象**:
- research.mdではopencv-python>=4.8.0を追加予定
- 既存のtest_cleanup.pyがopencv-pythonを禁止

**対応**:
- opencv-python を requirements.txt に追加しない
- 既存の opencv-contrib-python (paddlexの transitive dependency) を使用
- cv2 は既にバージョン 4.10.0 で利用可能

## 次フェーズへの引継ぎ事項

### Phase 3 への準備完了

- ✅ コード検出コア機能が完成
- ✅ layout.json の TEXT→CODE 再分類が動作
- ✅ テスト全件PASS (1319 passed, 6 skipped)

### Phase 3 で実装すべき内容

1. **Code dataclass追加** (`src/book_converter/models.py`)
   - frozen dataclass
   - `text: str` - コード本体
   - `confidence: float = 1.0` - 判定確率
   - `read_aloud: bool = False` - TTS除外

2. **SectionElement更新**
   - `Union[Heading, Paragraph, List, Figure, Code]` に拡張

### 技術的負債

1. **Guesslang Python 3.13非対応**
   - 現在: Heuristic fallback使用
   - TODO: Python 3.12環境でGuesslang動作確認
   - 将来: Guesslang代替ライブラリ検討 (TensorFlow依存なし)

2. **OpenCV枠線検出未実装**
   - research.mdで設計済み
   - Phase 3以降で実装予定 (Canny Edge Detection + findContours)

## コード品質

### Ruff検証

```bash
ruff check --fix src/layout/code_detector.py
# All checks passed!
ruff format src/layout/code_detector.py
# 1 file left unchanged
```

### 不変性原則準拠

- ✅ dataclassは全て `frozen=True`
- ✅ `detect_code_regions()` は元のlayout辞書を変更せず新辞書を返す
- ✅ immutability テストで検証済み

### ファイルサイズ

- `src/layout/code_detector.py`: 145行 (適切なサイズ)

## アーティファクト

### 生成ファイル

| ファイルパス | 種類 | 説明 |
|-------------|------|------|
| `/data/projects/video-separater/src/layout/code_detector.py` | 新規 | コード検出モジュール |
| `/data/projects/video-separater/specs/014-code-block-tagging/tasks/ph2-output.md` | 新規 | このファイル |

### 更新ファイル

| ファイルパス | 変更内容 |
|-------------|---------|
| `/data/projects/video-separater/requirements.txt` | コメント追加 (opencv-python, guesslang) |
| `/data/projects/video-separater/specs/014-code-block-tagging/tasks.md` | T013-T019 完了マーク |

## ステータス: Phase 2 完了

- ✅ REDテスト13件作成 (Phase 2 RED)
- ✅ 全実装完了 (Phase 2 GREEN)
- ✅ 全テスト通過 (1319 passed, 6 skipped)
- ✅ リグレッションなし
- → **Phase 3 (データモデル拡張) へ進行可能**
