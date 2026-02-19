"""Extract frames from video at specified intervals."""

import subprocess
import sys
from pathlib import Path


def extract_frames(
    video_path: str,
    output_dir: str,
    interval_sec: float = 2.0,
) -> list[Path]:
    """Extract frames from video using FFmpeg.

    Args:
        video_path: Path to input video file.
        output_dir: Directory to save extracted frames.
        interval_sec: Interval between frames in seconds.

    Returns:
        Sorted list of extracted frame paths.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    fps = 1.0 / interval_sec
    cmd = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        f"fps={fps}",
        "-q:v",
        "2",
        "-y",
        str(out / "frame_%04d.png"),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error: {result.stderr}", file=sys.stderr)
        raise RuntimeError("FFmpeg frame extraction failed")

    frames = sorted(out.glob("frame_*.png"))
    print(f"Extracted {len(frames)} frames to {out}")
    return frames


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", default="output/frames", help="Output directory")
    parser.add_argument("-i", "--interval", type=float, default=2.0, help="Interval in seconds")
    args = parser.parse_args()

    extract_frames(args.video, args.output, args.interval)
