"""Compute video file hash for output directory management."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HASH_PREFIX_LEN = 16
CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks for large files


def compute_video_hash(video_path: str, prefix_len: int = HASH_PREFIX_LEN) -> str:
    """Compute SHA-256 hash of a video file and return a prefix.

    Args:
        video_path: Path to the video file.
        prefix_len: Number of hex characters to return.

    Returns:
        Hex string prefix of the SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    with open(video_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()[:prefix_len]


def compute_full_hash(video_path: str) -> str:
    """Compute full SHA-256 hash of a video file.

    Args:
        video_path: Path to the video file.

    Returns:
        Full hex string of the SHA-256 hash.
    """
    sha256 = hashlib.sha256()
    with open(video_path, "rb") as f:
        while chunk := f.read(CHUNK_SIZE):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_source_info(output_dir: str, video_path: str, full_hash: str) -> Path:
    """Write source video metadata to source_info.json.

    Args:
        output_dir: Hash-based output directory.
        video_path: Original video file path.
        full_hash: Full SHA-256 hash of the video.

    Returns:
        Path to the created source_info.json.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    video = Path(video_path)
    info = {
        "video_path": str(video.resolve()),
        "video_name": video.name,
        "video_size_bytes": video.stat().st_size,
        "sha256": full_hash,
        "processed_at": datetime.now(timezone.utc).isoformat(),
    }

    info_path = out / "source_info.json"
    info_path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Source info saved to {info_path}")
    return info_path


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Compute video file hash")
    parser.add_argument("video", help="Input video file path")
    parser.add_argument(
        "--prefix-only", action="store_true", help="Output only the hash prefix"
    )
    args = parser.parse_args()

    if not Path(args.video).exists():
        print(f"Error: File not found: {args.video}", file=sys.stderr)
        sys.exit(1)

    full = compute_full_hash(args.video)
    prefix = full[:HASH_PREFIX_LEN]

    if args.prefix_only:
        print(prefix)
    else:
        print(f"SHA-256: {full}")
        print(f"Prefix:  {prefix}")
