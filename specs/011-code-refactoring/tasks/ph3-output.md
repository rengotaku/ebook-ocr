# Phase 3 出力: User Story 3 - 大規模ファイルの分割 (Priority: P3)

**日時**: 2026-02-18
**フェーズ**: Phase 3
**ステータス**: 完了

## サマリー

| 項目 | 結果 |
|------|------|
| 分割対象ファイル | 2件（ocr_ensemble.py: 699行, rover/engines.py: 613行） |
| 分割後のモジュール数 | ocr_ensemble: 4モジュール, rover/engines: 3モジュール |
| 最大ファイルサイズ | 438行（rover/engines/runners.py） |
| テスト結果 | 1306 passed, 6 skipped |
| ruff check | All checks passed! |
| ruff format | 46 files already formatted |

## 作業内容

### ocr_ensemble.py 分割（699行 → 4モジュール）

分割後の構造:
```
src/ocr_ensemble/
├── __init__.py      (235行) - 公開API re-export + 主要関数
├── models.py        (35行)  - データクラス
├── engines.py       (234行) - エンジン初期化・OCR実行
└── voting.py        (253行) - 品質検証・類似度計算・投票
```

#### models.py (35行)
- `EngineResult`: 単一エンジンの結果
- `EnsembleResult`: アンサンブル結果
- `TextWithBox`: テキスト + bbox情報

#### engines.py (234行)
- エンジン初期化関数: `_get_tesseract()`, `_get_easyocr_reader()`, `_get_paddleocr_reader()`, `_get_yomitoku_analyzer()`
- OCR実行関数: `ocr_tesseract()`, `ocr_easyocr()`, `ocr_paddleocr()`, `ocr_yomitoku_engine()`
- Bbox付きOCR: `ocr_paddleocr_with_boxes()`

#### voting.py (253行)
- 品質検証: `is_garbage()`
- Bbox操作: `bbox_iou()`, `bbox_contains()`
- マスク生成: `create_text_mask()`
- 類似度計算: `calculate_similarity()`, `calculate_similarity_matrix()`
- 投票・マージ: `vote_best_result()`, `merge_by_voting()`

#### __init__.py (235行)
- 公開API re-export（全関数・クラスを再公開）
- メイン関数: `ocr_ensemble()`, `run_ensemble_ocr()`, `main()`

### rover/engines.py 分割（613行 → 3モジュール）

分割後の構造:
```
src/rover/engines/
├── __init__.py      (32行)  - 公開API re-export
├── core.py          (196行) - エンジン初期化・データクラス・フィルタリング
└── runners.py       (438行) - エンジン実行・オーケストレーション
```

#### core.py (196行)
- エンジン初期化関数: `_get_tesseract()`, `_get_easyocr_reader()`, `_get_paddleocr_reader()`, `_get_yomitoku_analyzer()`
- データクラス: `TextWithBox`, `EngineResult`
- フィルタリング関数: `_is_word_inside_figures()`, `_is_item_inside_figures()`, `_filter_items_by_figures()`

#### runners.py (438行)
- エンジン実行関数: `run_yomitoku_with_boxes()`, `run_paddleocr_with_boxes()`, `run_easyocr_with_boxes()`, `run_tesseract_with_boxes()`
- オーケストレーション: `run_all_engines()`
- ヘルパー関数: `_cluster_words_to_lines()`, `_get_paragraph_confidence()`

#### __init__.py (32行)
- 公開API re-export（全関数・クラスを再公開）

### import文の更新

#### テストファイルの更新
**tests/test_ocr_engines.py**:
- mockパスを更新: `src.rover.engines._get_yomitoku_analyzer` → `src.rover.engines.runners._get_yomitoku_analyzer`
- mockパスを更新: `src.rover.engines._get_easyocr_reader` → `src.rover.engines.runners._get_easyocr_reader`

理由: プライベート関数は `core` モジュールに定義されているが、`runners` モジュールでインポートされて使用されているため、mockは使用箇所でパッチする必要がある。

#### 公開API維持
- **ocr_ensemble**: `__init__.py` でre-exportすることで、既存のimport文（`from src.ocr_ensemble import ...`）はすべて変更なしで動作
- **rover/engines**: 同様に `__init__.py` でre-exportすることで、既存のimport文はすべて変更なしで動作

## 検証結果

### T033: ruff check検証
```
$ ruff check src/
All checks passed!
```
✅ エラー0件

### T034: ruff format検証
```
$ ruff format --check src/
46 files already formatted
```
✅ 全ファイルフォーマット済

### T035: テスト実行
```
$ make test
1306 passed, 6 skipped in 23.55s
```
✅ 全テストパス（ベースライン1306件維持）

### T036: ocr_ensemble/ 行数検証
```
  234 src/ocr_ensemble/engines.py
  235 src/ocr_ensemble/__init__.py
   35 src/ocr_ensemble/models.py
  253 src/ocr_ensemble/voting.py
  757 total
```
✅ 全ファイルが600行以下

### T037: rover/engines/ 行数検証
```
  196 src/rover/engines/core.py
   32 src/rover/engines/__init__.py
  438 src/rover/engines/runners.py
  666 total
```
✅ 全ファイルが600行以下

## 変更ファイル一覧

| ファイル | 変更種別 | 行数 | 内容 |
|----------|----------|------|------|
| `src/ocr_ensemble/` | 新規作成 | - | ディレクトリ作成 |
| `src/ocr_ensemble/models.py` | 新規作成 | 35 | データクラス |
| `src/ocr_ensemble/engines.py` | 新規作成 | 234 | エンジン初期化・実行 |
| `src/ocr_ensemble/voting.py` | 新規作成 | 253 | 品質検証・投票 |
| `src/ocr_ensemble/__init__.py` | 新規作成 | 235 | 公開API + メイン関数 |
| `src/ocr_ensemble.py` | 削除 | - | 旧ファイル（699行） |
| `src/rover/engines/` | 新規作成 | - | ディレクトリ作成 |
| `src/rover/engines/core.py` | 新規作成 | 196 | エンジン初期化・データクラス |
| `src/rover/engines/runners.py` | 新規作成 | 438 | エンジン実行 |
| `src/rover/engines/__init__.py` | 新規作成 | 32 | 公開API re-export |
| `src/rover/engines.py` | 削除 | - | 旧ファイル（613行） |
| `tests/test_ocr_engines.py` | 修正 | - | mockパス更新 |

## 次フェーズへの引き継ぎ

### Phase 4（pre-commit設定）への準備完了

1. **ファイル分割完了**: 全ファイルが600行以下
2. **テストスイート維持**: 1306件のテストが全てパス
3. **公開API維持**: importパスは変更なし（`__init__.py`でre-export）
4. **コード品質維持**: ruff check/formatがエラー0件

### Phase 4で実施する内容

1. `.pre-commit-config.yaml` を作成（ruff check --fix + ruff format）
2. `pre-commit run --all-files` で検証

### 注意事項

- **内部構造の変更**: ファイル分割により内部構造は変更されたが、公開APIは維持されている
- **テストmockの更新**: 内部関数をmockするテストは、新しいモジュールパスに更新が必要だった
- **プライベート関数の可視性**: `_get_*` 関数は `core` モジュールに定義され、`runners` モジュールでインポートされて使用される

## 成果

### Success Criteria 達成状況

| SC | 内容 | 状態 |
|----|------|------|
| SC-004 | `src/` 配下のすべての `.py` ファイルが600行以下になる | ✅ 達成 |
| SC-005 | 既存のテストスイート（`pytest`）がすべてパスする | ✅ 達成 |
| SC-006 | ファイル分割前後でpublicなクラス・関数のimportパスが変更されない | ✅ 達成 |

**ステータス**: Phase 3 完了 ✅

## 技術的な学び

### re-exportパターンの有効性
`__init__.py` でre-exportすることで、内部構造を変更しながら公開APIを維持できた。これにより、既存コードの変更なしでリファクタリングが可能になった。

### mockパスの注意点
プライベート関数をmockする場合、関数が定義されている場所ではなく、使用されている場所でパッチする必要がある。今回のケースでは:
- 定義: `src.rover.engines.core._get_yomitoku_analyzer`
- 使用: `src.rover.engines.runners._get_yomitoku_analyzer`（インポート後）
- mockパス: `src.rover.engines.runners._get_yomitoku_analyzer`（使用箇所）

### ファイル分割の基準
- データクラス: 最小単位（35行）
- ドメイン単位: 初期化・実行・検証など、責務ごとに分割（200-450行）
- 公開API: re-exportと主要関数を集約（200-250行）
