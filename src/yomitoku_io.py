"""I/O utilities for Yomitoku OCR.

Helper functions for saving/loading yomitoku results and cache management.
Extracted from ocr_yomitoku.py to reduce file size.
"""

from __future__ import annotations

# Global analyzer instance for lazy initialization
_yomitoku_analyzer = None


def save_yomitoku_results(output_dir: str, page_stem: str, results) -> None:
    """Save yomitoku analysis results to cache.

    Args:
        output_dir: Output directory
        page_stem: Page filename stem (e.g., "page_0024")
        results: DocumentAnalyzerSchema from yomitoku
    """
    import pickle
    from pathlib import Path

    cache_dir = Path(output_dir) / "yomitoku_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{page_stem}.pkl"

    with open(cache_file, "wb") as f:
        pickle.dump(results, f)


def load_yomitoku_results(output_dir: str, page_stem: str):
    """Load yomitoku analysis results from cache.

    Args:
        output_dir: Output directory
        page_stem: Page filename stem (e.g., "page_0024")

    Returns:
        DocumentAnalyzerSchema or None if cache not found
    """
    import pickle
    from pathlib import Path

    cache_dir = Path(output_dir) / "yomitoku_cache"
    cache_file = cache_dir / f"{page_stem}.pkl"

    if not cache_file.exists():
        return None

    with open(cache_file, "rb") as f:
        return pickle.load(f)


def reset_analyzer() -> None:
    """Reset the cached analyzer instance.

    Call this if you need to change device or lite settings.
    """
    global _yomitoku_analyzer
    _yomitoku_analyzer = None
