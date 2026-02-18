"""Quality validation, similarity calculation, and voting functions for OCR ensemble."""

from __future__ import annotations

import re
from difflib import SequenceMatcher

from PIL import Image

from .models import EnsembleResult


def is_garbage(text: str, min_length: int = 50, ja_ratio_threshold: float = 0.1) -> bool:
    """Check if OCR result is garbage/invalid.

    Detection rules:
    1. Same character repeated 10+ times
    2. Japanese character ratio too low (for Japanese documents)
    3. Too many special characters

    Args:
        text: OCR result text.
        min_length: Minimum text length to check ratio (short texts are not checked).
        ja_ratio_threshold: Minimum Japanese character ratio.

    Returns:
        True if text appears to be garbage.
    """
    if not text:
        return True

    # Rule 1: Same character repeated 10+ times
    if re.search(r"(.)\1{9,}", text):
        return True

    # Rule 2: Japanese character ratio too low (only for longer texts)
    if len(text) >= min_length:
        ja_chars = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text))
        ja_ratio = ja_chars / len(text)
        if ja_ratio < ja_ratio_threshold:
            return True

    # Rule 3: Too many consecutive special characters
    if re.search(r"[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]{10,}", text):
        return True

    return False


def bbox_iou(bbox1: list[int], bbox2: list[int]) -> float:
    """Calculate Intersection over Union (IoU) of two bboxes.

    Args:
        bbox1: [x1, y1, x2, y2]
        bbox2: [x1, y1, x2, y2]

    Returns:
        IoU value (0.0 - 1.0)
    """
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    # Use float to avoid overflow
    intersection = float(x2 - x1) * float(y2 - y1)
    area1 = float(bbox1[2] - bbox1[0]) * float(bbox1[3] - bbox1[1])
    area2 = float(bbox2[2] - bbox2[0]) * float(bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def bbox_contains(outer: list[int], inner: list[int], threshold: float = 0.7) -> bool:
    """Check if outer bbox contains inner bbox.

    Args:
        outer: [x1, y1, x2, y2] - the containing bbox
        inner: [x1, y1, x2, y2] - the bbox to check
        threshold: Minimum overlap ratio of inner bbox

    Returns:
        True if inner is mostly contained in outer
    """
    x1 = max(outer[0], inner[0])
    y1 = max(outer[1], inner[1])
    x2 = min(outer[2], inner[2])
    y2 = min(outer[3], inner[3])

    if x2 <= x1 or y2 <= y1:
        return False

    # Use float to avoid overflow
    intersection = float(x2 - x1) * float(y2 - y1)
    inner_area = float(inner[2] - inner[0]) * float(inner[3] - inner[1])

    return (intersection / inner_area) >= threshold if inner_area > 0 else False


def create_text_mask(
    image: Image.Image,
    regions: list[dict],
    text_types: list[str] | None = None,
    fill_color: str = "white",
) -> Image.Image:
    """Create masked image with only TEXT-like regions visible.

    Strategy: Start with white canvas, paste only TEXT regions from original.
    This ensures everything outside TEXT regions is masked.

    Args:
        image: Original PIL Image.
        regions: List of region dicts with "type" and "bbox" keys.
        text_types: Region types to keep visible. Default: ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]
        fill_color: Color to fill masked areas.

    Returns:
        Masked PIL Image with only text regions visible.
    """
    if text_types is None:
        text_types = ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]

    # Start with white canvas
    masked = Image.new("RGB", image.size, color=fill_color)

    # Paste only TEXT regions from original image
    for region in regions:
        region_type = region.get("type", "")
        if region_type in text_types:
            bbox = region.get("bbox", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                # Crop from original and paste to masked
                text_region = image.crop((x1, y1, x2, y2))
                masked.paste(text_region, (x1, y1))

    return masked


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def calculate_similarity_matrix(results: dict[str, str]) -> dict[str, dict[str, float]]:
    """Calculate pairwise similarity between all engine results."""
    engines = list(results.keys())
    matrix: dict[str, dict[str, float]] = {}
    for e1 in engines:
        matrix[e1] = {}
        for e2 in engines:
            matrix[e1][e2] = calculate_similarity(results[e1], results[e2])
    return matrix


def vote_best_result(
    results: dict[str, str],
    similarity_matrix: dict[str, dict[str, float]],
    threshold: float = 0.7,
) -> tuple[str, str, dict[str, int]]:
    """Vote for the best result based on agreement between engines.

    Strategy:
    1. Calculate average similarity of each engine to others
    2. Engine with highest average similarity wins
    3. If all low similarity, prefer DeepSeek (best for Japanese)

    Returns:
        Tuple of (best_text, winning_engine, vote_counts).
    """
    engines = [e for e, t in results.items() if t]  # Only engines with results

    if not engines:
        return "", "none", {}

    if len(engines) == 1:
        return results[engines[0]], engines[0], {engines[0]: 1}

    # Calculate average agreement score for each engine
    scores: dict[str, float] = {}
    for engine in engines:
        other_sims = [similarity_matrix[engine][other] for other in engines if other != engine]
        scores[engine] = sum(other_sims) / len(other_sims) if other_sims else 0

    # Count "votes" - how many engines agree with each
    votes: dict[str, int] = {}
    for engine in engines:
        votes[engine] = sum(1 for other in engines if other != engine and similarity_matrix[engine][other] >= threshold)

    # Find winner
    max_votes = max(votes.values()) if votes else 0

    if max_votes > 0:
        # At least some agreement - pick engine with most votes
        # Tie-break by average similarity score
        winners = [e for e, v in votes.items() if v == max_votes]
        winner = max(winners, key=lambda e: scores.get(e, 0))
        return results[winner], winner, votes
    else:
        # No agreement - prefer by priority: yomitoku > paddleocr > easyocr > tesseract
        priority = ["yomitoku", "paddleocr", "easyocr", "tesseract"]
        for engine in priority:
            if engine in engines and results[engine]:
                return results[engine], engine, votes

        # Fallback to first available
        return results[engines[0]], engines[0], votes


def merge_by_voting(
    results: dict[str, str],
    threshold: float = 0.7,
) -> EnsembleResult:
    """Merge OCR results using voting strategy.

    Args:
        results: Dict of engine_name -> text.
        threshold: Similarity threshold for counting as agreement.

    Returns:
        EnsembleResult with merged text and metadata.
    """
    # Filter to successful results only
    valid_results = {k: v for k, v in results.items() if v}

    if not valid_results:
        return EnsembleResult(
            merged="",
            results=results,
            similarity_matrix={},
            source="none",
        )

    # Calculate similarities
    sim_matrix = calculate_similarity_matrix(valid_results)

    # Vote for best
    merged_text, winner, votes = vote_best_result(valid_results, sim_matrix, threshold)

    return EnsembleResult(
        merged=merged_text,
        results=results,
        similarity_matrix=sim_matrix,
        source=winner,
        votes=votes,
    )
