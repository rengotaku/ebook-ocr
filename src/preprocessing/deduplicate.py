"""Remove duplicate and transition frames using perceptual hashing."""

from pathlib import Path

import imagehash
from PIL import Image


def deduplicate_frames(
    frame_dir: str,
    output_dir: str,
    hash_threshold: int = 8,
    *,
    limit: int | None = None,
) -> list[Path]:
    """Remove duplicate frames based on perceptual hash similarity.

    Frames that are too similar to the previous unique frame are discarded.
    This handles page-turn animations and static duplicate frames.

    Args:
        frame_dir: Directory containing extracted frames.
        output_dir: Directory to save deduplicated frames.
        hash_threshold: Max hamming distance to consider frames as duplicates.
            Lower = stricter (fewer kept). 8 is a good default.
        limit: Process only first N files (for testing).

    Returns:
        Sorted list of unique frame paths.
    """
    import sys

    src = Path(frame_dir)
    dst = Path(output_dir)
    dst.mkdir(parents=True, exist_ok=True)

    frames = sorted(src.glob("frame_*.png"))
    if limit:
        print(f"Processing first {limit} of {len(frames)} files", file=sys.stderr)
        frames = frames[:limit]
    if not frames:
        print("No frames found")
        return []

    unique_frames: list[Path] = []
    prev_hash = None
    page_num = 1

    for frame_path in frames:
        with Image.open(frame_path) as img:
            current_hash = imagehash.phash(img)

            if prev_hash is not None:
                distance = current_hash - prev_hash
                if distance < hash_threshold:
                    continue

            out_path = dst / f"page_{page_num:04d}.png"
            img.save(out_path)
            unique_frames.append(out_path)
            prev_hash = current_hash
            page_num += 1

    removed = len(frames) - len(unique_frames)
    print(f"Kept {len(unique_frames)} unique pages, removed {removed} duplicates")
    return unique_frames


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deduplicate frames")
    parser.add_argument("input_dir", help="Directory with extracted frames")
    parser.add_argument("-o", "--output", default="output/pages", help="Output directory")
    parser.add_argument("-t", "--threshold", type=int, default=8, help="Hash distance threshold")
    args = parser.parse_args()

    deduplicate_frames(args.input_dir, args.output, args.threshold)
