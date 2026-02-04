# Phase 2 RED Tests

## サマリー
- Phase: Phase 2 - US1 共有ユーティリティ抽出・モジュール結合解消
- FAIL テスト数: 11 (collected 0 / 1 collection error due to ImportError)
- テストファイル: tests/test_utils.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_utils.py | TestEncodeImageFile::test_encode_image_file | base64エンコード結果をデコードすると元ファイルのバイト列と一致 |
| tests/test_utils.py | TestEncodeImageFile::test_encode_image_file_returns_str | 戻り値が str 型 |
| tests/test_utils.py | TestEncodePilImage::test_encode_pil_image_roundtrip | PIL Image -> base64 -> PIL Image のラウンドトリップでサイズ・モードが一致 |
| tests/test_utils.py | TestEncodePilImage::test_encode_pil_image_returns_str | 戻り値が str 型 |
| tests/test_utils.py | TestFormatFigureMarkers::test_format_figure_markers | page_0001.png に対して 2 つのマーカー(FIGURE+TABLE)が生成される |
| tests/test_utils.py | TestFormatFigureMarkers::test_format_figure_markers_contains_metadata | 出力に type, cropped_path, confidence 情報が含まれる |
| tests/test_utils.py | TestFormatFigureMarkers::test_format_figure_markers_empty | 存在しないページ名に対して空文字列 "" が返る |
| tests/test_utils.py | TestFormatFigureMarkers::test_format_figure_markers_low_confidence | min_confidence=0.9 で confidence=0.85 の TABLE エントリが除外される |
| tests/test_utils.py | TestMaskFigureRegions::test_mask_figure_regions | bbox [10,20,50,60] の領域が白(255,255,255)になる |
| tests/test_utils.py | TestMaskFigureRegions::test_mask_figure_regions_preserves_outside | マスク外のピクセルが元の灰色(200,200,200)のまま |
| tests/test_utils.py | TestMaskFigureRegions::test_mask_figure_regions_no_figures | 図なしページ → 元画像と同一オブジェクト(is) |
| tests/test_utils.py | TestMaskFigureRegions::test_mask_figure_regions_clamp | bbox [-10,-10,200,200] → クランプされて画像全体が白塗り |

## 実装ヒント

- `src/utils.py` を新規作成し、以下の 4 関数を実装する:
  - `encode_image_file(path: str) -> str` -- ファイルを読み込み base64.b64encode して str で返す
  - `encode_pil_image(img: Image.Image) -> str` -- PIL Image を PNG バイトに変換し base64 エンコード
  - `format_figure_markers(page_name: str, layout: dict, min_confidence: float = 0.7) -> str` -- layout dict からマーカー文字列を生成。page_name が存在しないか figures が空なら空文字列。confidence < min_confidence のエントリは除外
  - `mask_figure_regions(img: Image.Image, page_name: str, layout: dict) -> Image.Image` -- 図表領域を白塗りマスク。page_name に figures がなければ元画像をそのまま返す(同一オブジェクト)。bbox は画像境界にクランプする
- 既存実装の参照先:
  - `_encode_image`: src/ocr_deepseek.py:21-24, src/describe_figures.py:28-31
  - `_encode_pil_image`: src/ocr_deepseek.py:27-31
  - `_format_figure_markers`: src/ocr.py:96-119
  - `_mask_figure_regions`: src/ocr_deepseek.py:34-67 (crop_offset なし版を正とする)

## FAIL 出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collecting ... collected 0 items / 1 error

_____________________ ERROR collecting tests/test_utils.py _____________________
ImportError while importing test module 'tests/test_utils.py'.
tests/test_utils.py:16: in <module>
    from src.utils import (
E   ModuleNotFoundError: No module named 'src.utils'

=============================== 1 error in 0.08s ==============================
```
