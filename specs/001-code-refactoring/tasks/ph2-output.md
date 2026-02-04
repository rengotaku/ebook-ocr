# Phase 2 Output

## 作業概要
- Phase 2 - US1 共有ユーティリティ抽出・モジュール結合解消 の実装完了
- FAIL テスト 12 件を PASS させた
- モジュール結合 (`ocr_deepseek.py` → `ocr.py`) を完全に解消

## 修正ファイル一覧
- `src/utils.py` - 新規作成。4つの共有ユーティリティ関数を実装
  - `encode_image_file(path: str) -> str` - ファイルパスから base64 エンコード
  - `encode_pil_image(img: Image.Image) -> str` - PIL Image から base64 PNG エンコード
  - `format_figure_markers(page_name: str, layout: dict, min_confidence: float = 0.7) -> str` - 図表マーカーのフォーマット生成
  - `mask_figure_regions(img: Image.Image, page_name: str, layout: dict) -> Image.Image` - 図表領域の白塗りマスク処理

- `src/ocr_deepseek.py` - インポート修正、重複関数削除
  - `from src.ocr import _format_figure_markers` を削除
  - `from src.utils import ...` を追加
  - ローカル定義 `_encode_image`, `_encode_pil_image`, `_mask_figure_regions` を削除
  - 呼び出し箇所を `encode_image_file`, `encode_pil_image`, `format_figure_markers`, `mask_figure_regions` に更新
  - 不要な import (`base64`, `io`, `ImageDraw`) を削除

- `src/describe_figures.py` - インポート修正、重複関数削除
  - `from src.utils import encode_image_file` を追加
  - ローカル定義 `_encode_image` を削除
  - 呼び出し箇所を `encode_image_file` に更新
  - 不要な import (`base64`) を削除

## テスト結果

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collecting ... collected 12 items

tests/test_utils.py::TestEncodeImageFile::test_encode_image_file PASSED  [  8%]
tests/test_utils.py::TestEncodeImageFile::test_encode_image_file_returns_str PASSED [ 16%]
tests/test_utils.py::TestEncodePilImage::test_encode_pil_image_roundtrip PASSED [ 25%]
tests/test_utils.py::TestEncodePilImage::test_encode_pil_image_returns_str PASSED [ 33%]
tests/test_utils.py::TestFormatFigureMarkers::test_format_figure_markers PASSED [ 41%]
tests/test_utils.py::TestFormatFigureMarkers::test_format_figure_markers_contains_metadata PASSED [ 50%]
tests/test_utils.py::TestFormatFigureMarkers::test_format_figure_markers_empty PASSED [ 58%]
tests/test_utils.py::TestFormatFigureMarkers::test_format_figure_markers_low_confidence PASSED [ 66%]
tests/test_utils.py::TestMaskFigureRegions::test_mask_figure_regions PASSED [ 75%]
tests/test_utils.py::TestMaskFigureRegions::test_mask_figure_regions_preserves_outside PASSED [ 83%]
tests/test_utils.py::TestMaskFigureRegions::test_mask_figure_regions_no_figures PASSED [ 91%]
tests/test_utils.py::TestMaskFigureRegions::test_mask_figure_regions_clamp PASSED [100%]

============================== 12 passed in 0.03s
```

## インポート検証

`ocr_deepseek.py` が `ocr.py` に依存せずにインポート可能:

```bash
$ python -c "from src.ocr_deepseek import ocr_page_deepseek"
# エラーなし → 成功
```

## 注意点

### 次 Phase (Phase 3) への引き継ぎ
- `ocr.py` への依存が完全に解消されたため、Phase 3 でレガシーモジュール `src/ocr.py` を安全に削除可能
- `src/utils.py` には `_format_figure_markers` の実装が含まれているため、`ocr.py` の唯一の使用箇所だった依存が消滅

### 実装のポイント
- 関数名を公開関数名に変更 (`_encode_image` → `encode_image_file` など)
- `mask_figure_regions` は `ocr_deepseek.py` の実装を正としたため、図表がない場合に元画像をそのまま返す挙動を維持
- パイプラインの動作変更なし（出力同一性保証）

## 実装のミス・課題
- なし
