"""Preprocessing package for video frame extraction and deduplication.

Modules:
- frames: Frame extraction from video files
- deduplicate: Duplicate frame removal
- split_spread: Spread page splitting
- hash: Video file hashing
"""

from src.preprocessing import deduplicate, frames, hash, split_spread

__all__ = ["frames", "deduplicate", "split_spread", "hash"]
