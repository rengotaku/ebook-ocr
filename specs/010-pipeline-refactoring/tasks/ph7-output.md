# Phase 7 Output: Polish & クリーンアップ

**日付**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 7 - Polish & Cross-Cutting Concerns
**状態**: 完了（一部スキップあり）

## 作業サマリー

Phase 7では、新しいパッケージ構造への移行が完了した旧ファイルを削除し、コードベースのクリーンアップを実施しました。ただし、`src/ocr_yomitoku.py` については、まだ使用中のOCR関数が含まれているため削除をスキップしました。

### 完了したタスク

| タスク | 内容 | 状態 |
|--------|------|------|
| T098 | セットアップ分析読み込み | ✅ 完了 |
| T099 | 前フェーズ出力読み込み | ✅ 完了 |
| T100 | src/pipeline.py 削除 | ✅ 完了 |
| T101 | src/extract_frames.py 削除 | ✅ 完了 |
| T102 | src/deduplicate.py 削除 | ✅ 完了 |
| T103 | src/split_spread.py 削除 | ✅ 完了 |
| T104 | src/video_hash.py 削除 | ✅ 完了 |
| T105 | src/ocr_yomitoku.py 削除 | 🟡 スキップ |
| T106 | src/detect_figures.py 削除 | ✅ 完了 |
| T107 | src/reading_order.py 削除 | ✅ 完了 |
| T108 | src/ocr_rover.py 削除 | ✅ 完了 |
| T109 | src/ocr_engines.py 削除 | ✅ 完了 |
| T110 | src/ocr_alignment.py 削除 | ✅ 完了 |
| T111 | src/ocr_output.py 削除 | ✅ 完了 |
| T112 | 一時的wrapper削除 | ✅ 完了 (layout_detector.py) |
| T113 | quickstart.md検証 | ✅ 完了 |
| T114 | make test 実行 | ✅ 完了 (1306 passed) |
| T115 | src/構造確認 | ✅ 完了 |
| T116 | Phase出力生成 | ✅ 完了 |

**進捗**: 18/19タスク完了（1スキップ）

## 削除されたファイル

### 移行完了ファイル（削除済み）

| 旧ファイル | 移行先 | 削除状態 |
|-----------|--------|---------|
| `src/pipeline.py` | `src/cli/*.py` | ✅ 削除 |
| `src/extract_frames.py` | `src/preprocessing/frames.py` | ✅ 削除 |
| `src/deduplicate.py` | `src/preprocessing/deduplicate.py` | ✅ 削除 |
| `src/split_spread.py` | `src/preprocessing/split_spread.py` | ✅ 削除 |
| `src/video_hash.py` | `src/preprocessing/hash.py` | ✅ 削除 |
| `src/detect_figures.py` | `src/layout/figures.py` | ✅ 削除 |
| `src/reading_order.py` | `src/layout/reading_order.py` | ✅ 削除 |
| `src/ocr_rover.py` | `src/rover/ensemble.py` | ✅ 削除 |
| `src/ocr_engines.py` | `src/rover/engines.py` | ✅ 削除 |
| `src/ocr_alignment.py` | `src/rover/alignment.py` | ✅ 削除 |
| `src/ocr_output.py` | `src/rover/output.py` | ✅ 削除 |
| `src/layout_detector.py` | 一時的wrapper（不要） | ✅ 削除 |

**合計削除**: 12ファイル

### スキップされたファイル

| ファイル | 理由 | 次のアクション |
|---------|------|---------------|
| `src/ocr_yomitoku.py` | `ocr_page_yomitoku()` などのOCR関数が `layout_ocr.py` で使用中 | Phase 4で layout/detector.py に移行すべきだった機能の後続Issue作成 |

## 更新されたインポート

### CLIスクリプト

| ファイル | 更新内容 |
|---------|---------|
| `src/cli/extract_frames.py` | `from src.preprocessing.frames import extract_frames` |
| `src/cli/deduplicate.py` | `from src.preprocessing.deduplicate import deduplicate_frames` |
| `src/cli/split_spreads.py` | `from src.preprocessing.split_spread import ...` |
| `src/cli/detect_layout.py` | `from src.layout.detector import detect_layout` |
| `src/cli/run_ocr.py` | `from src.rover.ensemble import run_rover_batch` |

### ソースファイル

| ファイル | 更新内容 |
|---------|---------|
| `src/consolidate.py` | `from src.rover.output import ROVEROutput` |
| `src/layout_ocr.py` | `from src.layout.reading_order import ...` |

### テストファイル

| ファイル | 更新内容 |
|---------|---------|
| `tests/test_deduplicate.py` | `from src.preprocessing.deduplicate import ...` |
| `tests/test_split_spread.py` | `from src.preprocessing.split_spread import ...` |
| `tests/test_detect_figures.py` | `from src.layout.figures import ...` + importlib更新 |
| `tests/test_reading_order.py` | `from src.layout.reading_order import ...` |
| `tests/test_ocr_rover.py` | `from src.rover.ensemble import ...` |
| `tests/test_ocr_engines.py` | `from src.rover.engines import ...` + @patch更新 |
| `tests/test_ocr_alignment.py` | `from src.rover.alignment import ...` |

**合計更新**: 12ファイル

## 最終的なsrc/構造

```
src/
├── book_converter/       # 既存（変更なし）
├── cli/                  # Phase 2で作成（6つの独立CLIスクリプト）
│   ├── __init__.py
│   ├── __main__.py
│   ├── extract_frames.py
│   ├── deduplicate.py
│   ├── split_spreads.py
│   ├── detect_layout.py
│   ├── run_ocr.py
│   └── consolidate.py
├── rover/                # Phase 4で作成（OCR統合）
│   ├── __init__.py
│   ├── ensemble.py
│   ├── engines.py
│   ├── alignment.py
│   └── output.py
├── preprocessing/        # Phase 4で作成（前処理）
│   ├── __init__.py
│   ├── frames.py
│   ├── deduplicate.py
│   ├── split_spread.py
│   └── hash.py
├── layout/               # Phase 4で作成（レイアウト解析）
│   ├── __init__.py
│   ├── detector.py       # detect_layout_yomitoku のみ
│   ├── figures.py
│   └── reading_order.py
├── utils.py              # 既存（維持）
├── consolidate.py        # 既存（維持、CLIから参照）
├── ocr_ensemble.py       # 既存（維持）
├── ocr_integrated.py     # 既存（維持）
├── layout_ocr.py         # 既存（維持）
├── ocr_preprocess.py     # 既存（維持）
├── ocr_yomitoku.py       # 🟡 維持（OCR関数がまだ使用中）
└── __init__.py
```

**ディレクトリ数**: 5（book_converter, cli, rover, preprocessing, layout）
**src/直下のファイル**: 8（うち1つは削除予定）

## テスト結果

### make test 実行結果

```
======================= 1306 passed, 6 skipped in 17.65s =======================
```

**状態**: ✅ 全テストパス

### 構造確認

```bash
$ ls src/
book_converter  cli  consolidate.py  __init__.py  layout  layout_ocr.py
ocr_ensemble.py  ocr_integrated.py  ocr_preprocess.py  ocr_yomitoku.py
preprocessing  __pycache__  rover  utils.py
```

**状態**: ✅ 期待通りの構造

## 実装上の問題点

### T105: src/ocr_yomitoku.py の削除スキップ

**原因**:
- Phase 4で `src/layout/detector.py` に移行されたのは `detect_layout_yomitoku()` 関数のみ
- `ocr_page_yomitoku()`, `ocr_page_yomitoku_full()`, `ocr_pages_yomitoku()` などのOCR関数は移行されていない
- これらの関数は `src/layout_ocr.py` で現在も使用されている

**影響**:
- `src/ocr_yomitoku.py` を削除すると `layout_ocr.py` が動作しなくなる
- 23個のテスト (test_layout_ocr.py) が失敗する

**解決策（後続Issue）**:
1. `ocr_page_yomitoku()` およびOCR関連関数を適切なパッケージに移行
   - 候補A: `src/layout/detector.py` に追加（レイアウト検出とOCRを統合）
   - 候補B: `src/rover/yomitoku.py` を新規作成（yomitoku専用OCRモジュール）
2. `layout_ocr.py` のインポートを更新
3. `src/ocr_yomitoku.py` を削除

**現時点の対処**:
- `layout_ocr.py` のインポートは `from src.ocr_yomitoku import ...` のまま維持
- `src/ocr_yomitoku.py` は削除せず維持

## quickstart.md 検証結果

**ファイル**: `specs/010-pipeline-refactoring/quickstart.md`

**検証項目**:
- ✅ 全CLIコマンドが正しいモジュールパスを使用（`src.cli.*`）
- ✅ ワークフロー手順が明確
- ✅ トラブルシューティングセクションが充実
- ✅ 一括実行スクリプトが動作可能

**結論**: 問題なし。そのまま使用可能。

## 次フェーズへの引き継ぎ事項

Phase 7でリファクタリングは完了しましたが、以下の後続作業が推奨されます。

### 後続Issue 1: ocr_yomitoku.py の完全移行

**タイトル**: OCR関数を新パッケージ構造に移行

**内容**:
- `src/ocr_yomitoku.py` の OCR関数（`ocr_page_yomitoku` など）を適切なパッケージに移行
- `layout_ocr.py` のインポート更新
- `src/ocr_yomitoku.py` を削除

**優先度**: P2（中）

### 後続Issue 2: 残存ファイルのリファクタリング検討

**内容**:
- `src/ocr_ensemble.py`: 機能を `rover/` に統合可能か検討
- `src/ocr_integrated.py`: 機能を `rover/` に統合可能か検討
- `src/layout_ocr.py`: 機能を `layout/` に移動可能か検討
- `src/ocr_preprocess.py`: 機能を `preprocessing/` または `rover/` に移動可能か検討

**優先度**: P3（低）

### 後続Issue 3: ドキュメント更新

**内容**:
- プロジェクトREADME.mdにパッケージ構造の説明を追加
- アーキテクチャ図の作成（cli → preprocessing → layout → rover → consolidate）
- 各パッケージのREADME.md作成（オプション）

**優先度**: P3（低）

## まとめ

Phase 7 (Polish & クリーンアップ) を完了しました。

**達成事項**:
- ✅ 12個の旧ファイル削除（移行完了）
- ✅ 12個のインポート更新（CLI、ソース、テスト）
- ✅ 全テストパス (1306 passed, 6 skipped)
- ✅ 最終的なsrc/構造確認
- ✅ quickstart.md検証

**未完了事項**:
- 🟡 `src/ocr_yomitoku.py` の削除（OCR関数がまだ使用中のためスキップ）

**次のステップ**: 010-pipeline-refactoringフィーチャー完了。後続Issueで残存ファイルのリファクタリングを検討。
