# Phase 3 Output: 命名規則統一 (GREEN)

**日付**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 3 - User Story 2 (命名規則統一)

## Summary

| 項目 | 値 |
|------|-----|
| Phase | 3 |
| タスク完了 | 9/9 |
| テスト状態 | 1269 passed, 6 skipped |
| 状態 | GREEN |

## 作業内容

### 1. 命名規則の統一

**実施項目**:
- `yomitoku_device` → `device` への引数名変更
- `detect_layout_yomitoku` → `detect_layout` への関数名エイリアス作成
- CLI層での `ocr_yomitoku` モジュールインポート除去

### 2. 変更されたファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/cli/run_ocr.py` | `yomitoku_device=args.device` → `device=args.device` |
| `src/cli/detect_layout.py` | `from src.layout_detector import detect_layout` に変更 |
| `src/layout_detector.py` | **新規作成**: 一時的なラッパーモジュール（Phase 4で移動予定） |
| `src/ocr_yomitoku.py` | `detect_layout` エイリアス追加 |
| `src/ocr_rover.py` | 全ての `yomitoku_device` → `device` に変更 |
| `src/ocr_engines.py` | 全ての `yomitoku_device` → `device` に変更 |
| `src/layout_ocr.py` | 全ての `yomitoku_device` → `device` に変更 |
| `src/ocr_ensemble.py` | 全ての `yomitoku_device` → `device` に変更 |
| `src/ocr_integrated.py` | 全ての `yomitoku_device` → `device` に変更 |
| `src/pipeline.py` | 全ての `yomitoku_device` → `device` に変更、コメント・docstringも更新 |

### 3. 新規作成されたファイル

**src/layout_detector.py**:
- 目的: CLI層から `ocr_yomitoku` モジュールへの直接依存を除去
- 内容: `detect_layout_yomitoku` へのクリーンなインターフェース提供
- 将来計画: Phase 4で `src/layout/detector.py` に移動予定

## テスト結果

### 命名規則テスト (tests/test_naming_convention.py)

```
✅ TestYomitokuNamingInCLI::test_no_yomitoku_device_in_cli_args
✅ TestYomitokuNamingInCLI::test_no_yomitoku_in_argparse_dest
✅ TestYomitokuNamingInCLI::test_no_yomitoku_in_cli_variable_names
✅ TestYomitokuFunctionNaming::test_no_detect_layout_yomitoku_import_in_cli
✅ TestYomitokuFunctionNaming::test_no_yomitoku_function_calls_in_cli
✅ TestRoverOcrNaming::test_no_rover_ocr_in_module_names
✅ TestRoverOcrNaming::test_no_rover_ocr_in_code_comments
✅ TestGrepVerification::test_grep_no_yomitoku_device_in_cli
✅ TestGrepVerification::test_grep_no_detect_layout_yomitoku_in_cli
✅ TestGrepVerification::test_grep_no_ocr_yomitoku_import_in_cli
```

**全テスト**: 10/10 PASS

### 全体テスト

```
======================= 1269 passed, 6 skipped in 7.08s ========================
```

**リグレッション**: なし

## Phase 4への引き継ぎ事項

### 1. 一時的なモジュール構造

**src/layout_detector.py**:
- Phase 3で作成した一時的なラッパーモジュール
- Phase 4で `src/layout/detector.py` に統合される予定
- 削除条件: `src/layout/` パッケージ作成完了後

### 2. 残存する「yomitoku」名称

以下の箇所には「yomitoku」が残っているが、これらはPhase 4以降で対処:

**内部モジュール名**:
- `src/ocr_yomitoku.py` → `src/layout/detector.py` (Phase 4で移動)

**関数名** (`src/ocr_yomitoku.py` 内):
- `ocr_page_yomitoku()` → `ocr_page()` または `detect_text()` へリネーム検討
- `detect_layout_yomitoku()` → `detect_layout()` への完全移行（エイリアス除去）

**外部ライブラリ参照**:
- `from yomitoku import DocumentAnalyzer` - これは変更不要（外部依存）
- `_yomitoku_analyzer` 変数名 - 内部実装詳細として容認

**コメント・docstring**:
- 「yomitoku」への言及 - 技術的文脈（「yomitoku library使用」等）として必要

### 3. 命名規則の達成状況

**達成済み**:
- ✅ CLI層の公開インターフェースから `yomitoku_device` 除去完了
- ✅ CLI層から `ocr_yomitoku` モジュールへの直接インポート除去完了
- ✅ 全ソースファイルで `yomitoku_device` → `device` 変更完了

**Phase 4で完了予定**:
- ⏳ モジュール名の変更（`ocr_yomitoku.py` → `layout/detector.py`）
- ⏳ 関数名の完全統一（エイリアス除去）

## 検証結果

### grep検証

**CLI層のクリーンアップ確認**:
```bash
$ grep -r "yomitoku_device" src/cli/
# 結果: 0件
```

```bash
$ grep -r "from src.ocr_yomitoku" src/cli/
# 結果: 0件
```

**残存する「yomitoku」参照**:
- 140件（主に `src/ocr_yomitoku.py` 内の正当な使用）
- 内訳:
  - 外部ライブラリ `yomitoku` へのインポート: 適切
  - モジュール内の関数名: Phase 4で対処
  - 技術的コメント・docstring: 必要な文脈情報

## 技術的な決定事項

### layout_detector.py の作成理由

**問題**:
- Phase 3のスコープは「命名規則統一」のみ
- Phase 4が「フォルダ構造整理」（モジュールの移動・再編成）

**課題**:
- CLIテストは `from src.ocr_yomitoku` が存在しないことを要求
- しかし、Phase 3では `src/layout/` パッケージはまだ作成されない

**解決策**:
- 一時的なラッパーモジュール `src/layout_detector.py` を作成
- Phase 4で `src/layout/detector.py` に移行時、このファイルを削除
- CLI側のインポート文は Phase 4 で `from src.layout.detector import detect_layout` に更新

**メリット**:
1. Phase 3 のテストが全てパス
2. Phase 4 への移行がスムーズ
3. 各フェーズの責務が明確

## 次のステップ

**Phase 4: User Story 3 - フォルダ構造の整理**:

1. **パッケージ作成**:
   - `src/preprocessing/` パッケージ作成
   - `src/layout/` パッケージ作成
   - `src/rover/` パッケージ作成

2. **モジュール移動**:
   - `src/ocr_yomitoku.py` → `src/layout/detector.py`
   - `src/layout_detector.py` を削除（役割終了）
   - その他のモジュールも適切なパッケージへ移動

3. **インポート更新**:
   - `src/cli/detect_layout.py`: `from src.layout.detector import detect_layout`
   - その他全ファイルのインポートパス更新

4. **エイリアス除去**:
   - `detect_layout = detect_layout_yomitoku` を削除
   - 関数本体のリネームまたは統合

## まとめ

Phase 3では、命名規則統一の目標を達成しました:

**完了した作業**:
- ✅ T040-T045: 全実装タスク完了
- ✅ T046-T047: 全検証タスク完了
- ✅ T048: Phase出力生成

**成果**:
- CLI層から `yomitoku` 関連の命名を完全除去
- 全テストがパス（リグレッションなし）
- Phase 4への明確な引き継ぎ計画

**ステータス**: ✅ GREEN - Phase 4へ進行可能
