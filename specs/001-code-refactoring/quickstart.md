# Quickstart: コードベースリファクタリング

**Branch**: `001-code-refactoring`

## Prerequisites

- Python 3.13+
- `make setup` 実行済み（venv + 依存パッケージ）

## 実装フロー

### Phase 1: 共有ユーティリティ抽出 (P1)

TDD サイクル:

```bash
# 1. テストを先に書く (RED)
# tests/test_utils.py を作成
make test  # → FAIL (src/utils.py が存在しない)

# 2. src/utils.py を作成して関数を移動 (GREEN)
# - encode_image_file()    ← ocr_deepseek.py, describe_figures.py から
# - encode_pil_image()     ← ocr_deepseek.py から
# - format_figure_markers() ← ocr.py から
# - mask_figure_regions()   ← ocr_deepseek.py から (crop_offset なし版)
make test  # → PASS

# 3. 既存モジュールのインポートを更新
# ocr_deepseek.py: from src.ocr import → from src.utils import
# ocr_deepseek.py: ローカル _encode_image, _mask_figure_regions 削除
# describe_figures.py: ローカル _encode_image 削除

# 4. パイプライン動作確認
make run VIDEO="movies/test.mov"  # 出力が変わらないことを確認
```

### Phase 2: デッドコード除去 (P2)

```bash
# 1. src/ocr.py を削除
rm src/ocr.py

# 2. requirements.txt から不要依存を削除
# easyocr, pytesseract, opencv-python を削除

# 3. コードベース全体で未使用インポートがないか確認
grep -r "from src.ocr " src/  # → 0 件であること
grep -r "import easyocr\|import pytesseract\|import cv2" src/  # → 0 件

# 4. テスト実行
make test  # → PASS
```

### Phase 3: テストスイート導入 (P3)

```bash
# 1. 各モジュールのテストを TDD で作成
# tests/test_deduplicate.py
# tests/test_ocr_deepseek.py (Ollama モック)
# tests/test_describe_figures.py (Ollama モック)

# 2. リソース管理パターン適用
# Image.open() → with Image.open() as img:

# 3. 全テスト実行
make test  # → ALL PASS
```

## 検証コマンド

```bash
# テスト実行
make test

# 重複関数チェック（各関数が1箇所のみに存在すること）
grep -rn "def encode_image_file\|def _encode_image" src/
grep -rn "def format_figure_markers\|def _format_figure_markers" src/
grep -rn "def mask_figure_regions\|def _mask_figure_regions" src/

# レガシー依存チェック
grep -E "easyocr|pytesseract|opencv-python" requirements.txt  # → 0 件

# プライベート関数クロスインポートチェック
grep -rn "from src\.\w\+ import _" src/  # → 0 件
```
