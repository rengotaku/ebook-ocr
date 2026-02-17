# API Contracts: ROVER OCR再設計

**Date**: 2026-02-14 | **Branch**: `008-rover-redesign`

## Module: `ocr_preprocess.py` (NEW)

### `apply_clahe`

EasyOCR用のCLAHE前処理。

```python
def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_size: int = 8,
) -> np.ndarray:
    """Apply CLAHE preprocessing for EasyOCR.

    Args:
        image: RGB image array (H, W, 3), dtype=uint8
        clip_limit: Threshold for contrast limiting (default: 2.0)
        tile_size: Grid size for histogram equalization (default: 8)

    Returns:
        Preprocessed RGB image array (H, W, 3), dtype=uint8

    Example:
        >>> import numpy as np
        >>> img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        >>> result = apply_clahe(img)
        >>> assert result.shape == img.shape
    """
```

---

## Module: `ocr_engines.py` (UPDATE)

### `run_yomitoku_with_boxes` (UPDATE)

`words`から信頼度を取得するように更新。

```python
def run_yomitoku_with_boxes(
    image: Image.Image,
    device: str = "cpu",
) -> EngineResult:
    """Run Yomitoku OCR with bounding boxes and confidence scores.

    Args:
        image: PIL Image to process.
        device: Device to use ("cuda" or "cpu").

    Returns:
        EngineResult with text, bboxes, and confidence from words.rec_score.

    Changes from current:
        - Uses results.words for confidence (rec_score)
        - Maps word confidence to paragraph via coordinate matching
    """
```

### `run_easyocr_with_boxes` (UPDATE)

CLAHE前処理を追加。

```python
def run_easyocr_with_boxes(
    image: Image.Image,
    lang_list: list[str] | None = None,
    apply_preprocessing: bool = True,  # NEW
) -> EngineResult:
    """Run EasyOCR with bounding boxes.

    Args:
        image: PIL Image to process.
        lang_list: Language list for EasyOCR.
        apply_preprocessing: Apply CLAHE preprocessing (default: True).

    Returns:
        EngineResult with text and bboxes.

    Changes from current:
        - Applies CLAHE preprocessing by default
    """
```

### `run_all_engines` (UPDATE)

Tesseract除外、ROVER参加エンジンのみ。

```python
def run_all_engines(
    image: Image.Image,
    engines: list[str] | None = None,  # Default changed
    yomitoku_device: str = "cpu",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
) -> dict[str, EngineResult]:
    """Run all specified OCR engines.

    Args:
        image: PIL Image to process.
        engines: List of engine names. Default: ["yomitoku", "paddleocr", "easyocr"]
                 (Tesseract removed from default)
        ...

    Returns:
        Dict mapping engine name to EngineResult.

    Changes from current:
        - Default engines exclude tesseract
        - tesseract_lang parameter removed
    """
```

---

## Module: `ocr_alignment.py` (NEW)

文字レベルアライメントと投票を担当する新規モジュール。

### `align_texts_character_level`

複数テキストを文字レベルでアライメント。

```python
def align_texts_character_level(
    texts: dict[str, str],  # engine -> text
) -> list[AlignedPosition]:
    """Align multiple texts at character level using difflib.

    Args:
        texts: Dict mapping engine name to text.

    Returns:
        List of AlignedPosition objects, one per aligned position.

    Algorithm:
        1. Select longest text as base
        2. Align each other text to base using SequenceMatcher
        3. Merge alignments into unified position list
    """
```

### `weighted_vote_character`

単一位置での信頼度重み付き投票。

```python
def weighted_vote_character(
    candidates: dict[str, str],  # engine -> char (None = gap)
    confidences: dict[str, float],  # engine -> confidence
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """Vote for best character at a single position.

    Args:
        candidates: Dict of engine -> character.
        confidences: Dict of engine -> confidence.
        engine_weights: Weight for each engine.

    Returns:
        Tuple of (voted_char, vote_weight).

    Formula:
        weight = engine_weights[engine] * confidences[engine]
        votes[char] += weight
        result = max(votes, key=votes.get)
    """
```

### `vote_aligned_text`

アライメントされた全位置を投票で統合。

```python
def vote_aligned_text(
    aligned_positions: list[AlignedPosition],
    confidences: dict[str, float],
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """Vote across all aligned positions to produce final text.

    Args:
        aligned_positions: List of AlignedPosition objects.
        confidences: Dict of engine -> confidence.
        engine_weights: Weight for each engine.

    Returns:
        Tuple of (voted_text, average_confidence).
    """
```

---

## Module: `ocr_rover.py` (MAJOR REWRITE)

### Constants

```python
# Engine weights for voting (higher = more trusted)
ENGINE_WEIGHTS: dict[str, float] = {
    "yomitoku": 1.5,
    "paddleocr": 1.2,
    "easyocr": 1.0,
}

# Garbage filter thresholds
MIN_CONFIDENCE: float = 0.5
MAX_REPEAT_CHARS: int = 5
MIN_ASCII_LENGTH: int = 5
```

### `normalize_text`

テキスト正規化（NFKC + 空白）。

```python
def normalize_text(text: str) -> str:
    """Normalize text for comparison.

    Args:
        text: Input text.

    Returns:
        NFKC normalized text with whitespace collapsed.
    """
```

### `calculate_similarity`

類似度計算（正規化後）。

```python
def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity ratio (0.0 - 1.0).

    Note:
        Both texts are normalized before comparison.
    """
```

### `is_garbage`

ゴミ判定。

```python
def is_garbage(
    text: str,
    confidence: float,
    min_confidence: float = MIN_CONFIDENCE,
) -> bool:
    """Check if text is garbage output.

    Args:
        text: Text to check.
        confidence: Confidence score.
        min_confidence: Minimum confidence threshold.

    Returns:
        True if text is garbage.

    Garbage criteria:
        - Empty or whitespace-only
        - confidence < min_confidence
        - No Japanese chars and len <= MIN_ASCII_LENGTH
        - Same character repeated >= MAX_REPEAT_CHARS times
    """
```

### `cluster_lines_by_y`

y座標で行クラスタリング。

```python
def cluster_lines_by_y(
    items: list[TextWithBox],
    y_tolerance: int = 20,
) -> list[OCRLine]:
    """Cluster text items into lines by y-coordinate.

    Args:
        items: List of text items with bboxes.
        y_tolerance: Maximum vertical distance for same line.

    Returns:
        List of OCRLine objects.
    """
```

### `align_lines_by_y`

複数エンジンの行をy座標でアライメント。

```python
def align_lines_by_y(
    lines_by_engine: dict[str, list[OCRLine]],
    y_tolerance: int = 30,
) -> list[AlignedLine]:
    """Align lines from multiple engines by y-coordinate.

    Args:
        lines_by_engine: Dict mapping engine name to list of OCRLine.
        y_tolerance: Maximum vertical distance to align.

    Returns:
        List of AlignedLine objects.
    """
```

### `vote_line_text` (UPDATED: True ROVER)

文字レベル投票で最良テキストを選択。

```python
def vote_line_text(
    aligned_line: AlignedLine,
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, list[str], float]:
    """Vote for best text using character-level alignment.

    Args:
        aligned_line: Aligned line with multiple engine results.
        engine_weights: Weight for each engine.

    Returns:
        Tuple of (voted_text, source_engines, final_confidence).

    Algorithm (True ROVER):
        1. Extract texts from each engine's line
        2. Align texts at character level (difflib.SequenceMatcher)
        3. For each position, vote with weight = engine_weight * confidence
        4. Concatenate voted characters
        5. Return final text with contributing engines
    """
```

### `rover_merge` (UPDATED: True ROVER)

真のROVERアルゴリズムによる統合処理。

```python
def rover_merge(
    engine_results: dict[str, EngineResult],
    primary_engine: str = "yomitoku",
    y_tolerance: int = 30,
    min_confidence: float = MIN_CONFIDENCE,
) -> ROVERResult:
    """Merge OCR results using True ROVER algorithm.

    Args:
        engine_results: Dict mapping engine name to EngineResult.
        primary_engine: Primary engine for baseline.
        y_tolerance: Maximum vertical distance for line alignment.
        min_confidence: Minimum confidence for garbage filter.

    Returns:
        ROVERResult with merged text and metadata.

    Algorithm (True ROVER):
        1. Apply garbage filter (conf < 0.5) to each engine's items
        2. Cluster items into lines per engine
        3. Align lines across engines by y-coordinate
        4. For each aligned line:
           a. Character-level alignment (difflib.SequenceMatcher)
           b. Weighted voting at each position:
              weight = engine_weights[engine] * confidence
           c. Concatenate voted characters
        5. Concatenate non-empty lines
    """
```

### `run_rover_ocr`

単一画像のROVER処理。

```python
def run_rover_ocr(
    image: Image.Image | str,
    engines: list[str] | None = None,
    primary_engine: str = "yomitoku",
    yomitoku_device: str = "cpu",
    min_confidence: float = MIN_CONFIDENCE,
) -> ROVERResult:
    """Run ROVER OCR on a single image.

    Args:
        image: PIL Image or path to image file.
        engines: List of engine names (default: yomitoku, paddleocr, easyocr).
        primary_engine: Primary engine for gap detection.
        yomitoku_device: Device for Yomitoku.
        min_confidence: Minimum confidence threshold.

    Returns:
        ROVERResult with merged text.
    """
```

### `run_rover_batch`

バッチ処理。

```python
def run_rover_batch(
    pages_dir: str,
    output_dir: str,
    engines: list[str] | None = None,
    primary_engine: str = "yomitoku",
    yomitoku_device: str = "cpu",
    min_confidence: float = MIN_CONFIDENCE,
) -> list[tuple[str, ROVERResult]]:
    """Run ROVER OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output files.
        engines: List of engine names.
        primary_engine: Primary engine.
        yomitoku_device: Device for Yomitoku.
        min_confidence: Minimum confidence threshold.

    Returns:
        List of (page_name, ROVERResult) tuples.

    Side effects:
        - Saves raw outputs to {output_dir}/raw/{engine}/{page_name}.txt
        - Saves ROVER outputs to {output_dir}/rover/{page_name}.txt
    """
```

---

## CLI Interface

### `ocr_rover.py --help`

```
usage: ocr_rover.py [-h] [-o OUTPUT] [--engines ENGINES]
                    [--primary PRIMARY] [--device {cpu,cuda}]
                    [--min-confidence MIN_CONFIDENCE]
                    pages_dir

ROVER OCR: Multi-engine voting for improved accuracy

positional arguments:
  pages_dir             Directory containing page images

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output directory (default: ocr_output)
  --engines ENGINES     Comma-separated list of engines
                        (default: yomitoku,paddleocr,easyocr)
  --primary PRIMARY     Primary engine for baseline (default: yomitoku)
  --device {cpu,cuda}   Device for Yomitoku (default: cpu)
  --min-confidence MIN_CONFIDENCE
                        Minimum confidence threshold (default: 0.5)
```

---

## Error Handling

| Error | Condition | Response |
|-------|-----------|----------|
| ImageLoadError | 画像ファイル読み込み失敗 | ログ記録、スキップ |
| EngineError | エンジン処理失敗 | EngineResult.success=False |
| NoResultsError | 全エンジンが空結果 | 空のROVERResult |
| InvalidConfidence | confidence範囲外 | 0.0にクリップ |
