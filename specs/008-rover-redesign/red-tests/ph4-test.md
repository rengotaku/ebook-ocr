# Phase 4 テスト実装 (RED)

**Date**: 2026-02-14
**Phase**: 4 - US4 (処理前後の比較可能性)
**Status**: RED (テストFAIL確認済み)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 4 |
| User Story | US4: 処理前後の比較可能性 |
| FAIL テスト数 | 13件 |
| SKIP テスト数 | 2件 |
| PASS テスト数 | 87件 (既存Phase 2, 3テスト) |
| テストファイル | 3ファイル (新規2, 更新1) |

## テストファイル一覧

| ファイル | 種類 | テスト数 | 説明 |
|----------|------|----------|------|
| tests/test_ocr_preprocess.py | 新規 | 13 | CLAHE前処理テスト |
| tests/test_ocr_engines.py | 新規 | 16 | エンジン固有機能テスト |
| tests/test_ocr_rover.py | 更新 | +15 | raw/rover出力テスト追加 |

## FAIL テスト一覧

### tests/test_ocr_preprocess.py (13件 FAIL)

| テストメソッド | 期待される動作 | FAIL理由 |
|---------------|--------------|----------|
| test_apply_clahe_shape_preserved | 出力shapeが入力と一致 | NotImplementedError |
| test_apply_clahe_dtype_preserved | 出力dtypeがuint8維持 | NotImplementedError |
| test_apply_clahe_returns_ndarray | ndarray型を返す | NotImplementedError |
| test_apply_clahe_contrast_enhanced | コントラスト向上 | NotImplementedError |
| test_apply_clahe_custom_clip_limit | カスタムclip_limit使用可能 | NotImplementedError |
| test_apply_clahe_custom_tile_size | カスタムtile_size使用可能 | NotImplementedError |
| test_apply_clahe_rgb_image | RGB画像処理 | NotImplementedError |
| test_apply_clahe_grayscale_values | グレースケール風画像処理 | NotImplementedError |
| test_apply_clahe_black_image | 全黒画像処理 | NotImplementedError |
| test_apply_clahe_white_image | 全白画像処理 | NotImplementedError |
| test_apply_clahe_typical_document_size | 典型的サイズ (480x640) 処理 | NotImplementedError |
| test_apply_clahe_small_image | 小さい画像 (4x4) 処理 | NotImplementedError |
| test_apply_clahe_default_parameters | デフォルトパラメータで動作 | NotImplementedError |

### tests/test_ocr_engines.py (2件 SKIP)

| テストメソッド | 期待される動作 | SKIP理由 |
|---------------|--------------|----------|
| test_easyocr_with_clahe_preprocessing | CLAHE前処理が適用される | apply_preprocessingパラメータ未実装 |
| test_easyocr_without_clahe_preprocessing | CLAHE前処理なし | apply_preprocessingパラメータ未実装 |

## 実装ヒント

### apply_clahe (src/ocr_preprocess.py)

```python
import cv2
import numpy as np

def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_size: int = 8,
) -> np.ndarray:
    # 1. RGB -> LAB変換
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    # 2. CLAHE作成
    clahe = cv2.createCLAHE(
        clipLimit=clip_limit,
        tileGridSize=(tile_size, tile_size)
    )

    # 3. Lチャンネルに適用
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])

    # 4. LAB -> RGB変換
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
```

### run_easyocr_with_boxes 更新 (src/ocr_engines.py)

```python
def run_easyocr_with_boxes(
    image: Image.Image,
    lang_list: list[str] | None = None,
    apply_preprocessing: bool = True,  # NEW
) -> EngineResult:
    # ...
    if apply_preprocessing:
        from ocr_preprocess import apply_clahe
        img_array = apply_clahe(img_array)
    # ...
```

### run_rover_batch 更新 (src/ocr_rover.py)

```python
def run_rover_batch(...):
    # raw出力: {output_dir}/raw/{engine}/{page_name}.txt
    # rover出力: {output_dir}/rover/{page_name}.txt
```

## FAIL出力例

```
FAILED tests/test_ocr_preprocess.py::TestApplyCLAHE::test_apply_clahe_shape_preserved - NotImplementedError: apply_clahe not yet implemented
FAILED tests/test_ocr_preprocess.py::TestApplyCLAHE::test_apply_clahe_dtype_preserved - NotImplementedError: apply_clahe not yet implemented
...
=================== 13 failed, 87 passed, 2 skipped in 0.13s ===================
```

## テスト実行コマンド

```bash
# Phase 4テストのみ
pytest tests/test_ocr_preprocess.py tests/test_ocr_engines.py tests/test_ocr_rover.py -v

# 全テスト
make test
```

## 実装後の期待結果

- tests/test_ocr_preprocess.py: 13件 PASS
- tests/test_ocr_engines.py: 16件 PASS (SKIP解消)
- tests/test_ocr_rover.py: 既存56件 + 新規15件 = 71件 PASS

## 次のステップ

1. phase-executor が Implementation (GREEN) を実行
2. `src/ocr_preprocess.py` に `apply_clahe` を実装
3. `src/ocr_engines.py` を更新 (yomitoku words信頼度、easyocr CLAHE)
4. `src/ocr_rover.py` を更新 (run_rover_batch raw/rover出力)
5. `make test` PASS (GREEN) を確認
6. Verification フェーズへ進行

## 依存関係

- **opencv-python**: CLAHE処理に必要 (`cv2.createCLAHE`)
- **numpy**: 画像配列処理

```bash
pip install opencv-python
```

## テスト設計方針

1. **単体テスト優先**: 各関数を独立してテスト
2. **モック使用**: 外部依存 (OCRエンジン) はモックで代替
3. **エッジケース**: 空画像、小画像、大画像を網羅
4. **ファイルI/Oテスト**: tmp_pathフィクスチャで一時ディレクトリ使用
