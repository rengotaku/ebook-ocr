# Research: コードベースリファクタリング

**Date**: 2026-02-04
**Branch**: `001-code-refactoring`

## R-001: 共有ユーティリティに移動する関数の特定

### Decision
以下の3関数を `src/utils.py` に移動する:

1. **`_encode_image(path: str) -> str`** — ファイルパスから base64 エンコード
   - 現在の場所: `ocr_deepseek.py:21-24`, `describe_figures.py:28-31`
   - 実装は完全に同一
   - 移動後の公開名: `encode_image_file()`（プライベート接頭辞を除去、用途を明確化）

2. **`_format_figure_markers(page_name, layout, min_confidence) -> str`**
   - 現在の場所: `ocr.py:96-119`（唯一の定義）
   - 呼び出し元: `ocr_deepseek.py:232`（`from src.ocr import _format_figure_markers`）
   - 移動後の公開名: `format_figure_markers()`

3. **`_mask_figure_regions(img, page_name, layout, ...) -> Image`**
   - 現在の場所: `ocr.py:9-46`（crop_offset 引数あり）、`ocr_deepseek.py:34-67`（crop_offset なし）
   - `ocr_deepseek.py` 版を正とする（アクティブパス。v3 は前処理なしで crop_offset 不要）
   - `ocr.py` 版の `crop_offset` パラメータは v1/v2 レガシー用であり不要
   - 移動後の公開名: `mask_figure_regions()`

### Rationale
- 重複排除で保守性向上（DRY 原則）
- `ocr_deepseek.py` → `ocr.py` の結合を解消
- プライベート関数を公開ユーティリティに昇格（テスト容易性向上）

### Alternatives Considered
- **`src/image_utils.py` + `src/layout_utils.py` に分割**: YAGNI 違反。関数が3つしかないため1ファイルで十分
- **既存モジュールに統合**: どのモジュールにも属さない横断的関数のため、新規 utils が適切

---

## R-002: `_encode_pil_image()` の扱い

### Decision
`_encode_pil_image()` (ocr_deepseek.py:27-31) は `src/utils.py` に移動する。

### Rationale
- 現在 `ocr_deepseek.py` でのみ使用されているが、base64 エンコーディングのバリエーションとして `encode_image_file()` と同じモジュールに配置するのが自然
- 移動後の公開名: `encode_pil_image()`

### Alternatives Considered
- **`ocr_deepseek.py` に残す**: 機能的にはユーティリティ関数であり、他モジュールでも再利用可能なため移動が望ましい

---

## R-003: レガシー依存の除去判定

### Decision
以下の依存を `requirements.txt` から削除する:

| Package | 理由 |
|---------|------|
| `easyocr` | `ocr.py` でのみ使用。`ocr.py` 削除に伴い不要 |
| `pytesseract` | `ocr.py` でのみ使用。同上 |
| `opencv-python` | `src/` 内で直接 import されていない。constitution で「画像処理: Pillow, OpenCV」と記載あるが、現在の v3 パイプラインでは Pillow のみ使用 |

### Rationale
- v3 パイプラインでは DeepSeek-OCR (Ollama) が唯一の OCR エンジン
- `opencv-python` は constitution に記載があるが、実際のコードでは使用されていない
- constitution の Technical Constraints は将来の使用可能性を示すが、現在不要なら削除し、必要時に再追加する（YAGNI）

### Alternatives Considered
- **`opencv-python` を残す**: constitution 記載のため。ただし実コードで未使用のため YAGNI 原則に反する → 削除して constitution も更新

---

## R-004: `_detect_repetition()` の配置

### Decision
`_detect_repetition()` は `ocr_deepseek.py` に残す。

### Rationale
- OCR 出力の品質チェックであり、DeepSeek-OCR 固有のロジック
- 他モジュールからの再利用見込みなし
- 移動するメリットがない

---

## R-005: テスト戦略

### Decision
pytest を使用し、以下の構成でテストを作成する:

1. **`tests/test_utils.py`**: 共有ユーティリティの単体テスト
   - `encode_image_file()`: 既知画像ファイルの base64 エンコード検証
   - `encode_pil_image()`: PIL Image → base64 ラウンドトリップ検証
   - `format_figure_markers()`: 各種 layout 入力に対する出力検証
   - `mask_figure_regions()`: 白塗りマスクの座標検証

2. **`tests/test_deduplicate.py`**: 重複除去の単体テスト
   - 同一画像 → 重複検出
   - 異なる画像 → 非重複

3. **`tests/test_ocr_deepseek.py`**: OCR の統合テスト（Ollama モック）
   - `ocr_page_deepseek()`: API レスポンスモックでの出力検証
   - `_detect_repetition()`: 反復検出ロジック検証

4. **`tests/test_describe_figures.py`**: 図表説明のテスト（Ollama モック）
   - マーカー正規表現のマッチ検証
   - `_describe_single()`: API レスポンスモックでの出力検証

### Rationale
- TDD 必須（constitution II）: テスト先行で実装
- 外部 API (Ollama, FFmpeg) はモック化してテストの独立性を確保
- `test/` ディレクトリの既存データは参照データとして活用（手動テスト用として保持）

### Alternatives Considered
- **FFmpeg を含む E2E テスト**: 動画ファイルが必要でテスト時間が長い → モック化を優先
- **`test/` ディレクトリを `tests/` にリネーム**: 既存の参照データ構造を壊す → 別ディレクトリに新規作成

---

## R-006: Makefile テストターゲット追加

### Decision
Makefile に `test` ターゲットを追加する:

```makefile
test: setup  ## Run tests
	$(PYTHON) -m pytest tests/ -v
```

### Rationale
- constitution の「ビルド/テスト: Makefile」に準拠
- `make test` でテスト実行可能にする

---

## R-007: リソース管理パターン (FR-008)

### Decision
`Image.open()` の戻り値に対してコンテキストマネージャ（`with` 文）を適用する対象:

- `deduplicate.py:42` — `img = Image.open(frame_path)`
- `ocr_deepseek.py:206` — `raw_img = Image.open(page_path)`

### Rationale
- 大量画像処理時のファイルディスクリプタリーク防止
- Python の Pillow は `with` 文をサポート

### Alternatives Considered
- **明示的 `img.close()` 呼び出し**: `with` 文の方が例外安全
