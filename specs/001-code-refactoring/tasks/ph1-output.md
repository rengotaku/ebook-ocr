# Phase 1 Output

## 作業概要
- テスト基盤の初期化と Makefile 更新を実施

## 修正ファイル一覧
- `requirements.txt` — pytest を追加
- `Makefile` — `test` ターゲットを追加 (`$(PYTHON) -m pytest tests/ -v`)
- `tests/__init__.py` — 新規作成（空ファイル）
- `tests/conftest.py` — 新規作成（共有 fixtures: sample_image, sample_pil_image, sample_layout）

## 確認事項
- 重複関数の場所を確認:
  - `_encode_image`: ocr_deepseek.py:21-24, describe_figures.py:28-31（同一実装）
  - `_encode_pil_image`: ocr_deepseek.py:27-31（ocr_deepseek のみ）
  - `_format_figure_markers`: ocr.py:96-119（ocr.py のみ、ocr_deepseek.py から import）
  - `_mask_figure_regions`: ocr.py:9-46（crop_offset あり）, ocr_deepseek.py:34-67（crop_offset なし）
- pipeline.py は ocr.py を直接 import していない（ocr_deepseek.py 経由のみ）
- deduplicate.py:42 で `Image.open()` がコンテキストマネージャなしで使用

## 注意点
- `make test` はまだテストファイルが存在しないため空結果になる
- Phase 2 で src/utils.py を作成し、テストを先行で書く（TDD）
