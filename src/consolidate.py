"""Consolidate OCR outputs into book.txt and book.md.

This script combines individual page OCR results from layout-aware OCR into:
- book.txt: Plain text with page markers
- book.md: Markdown (OCR output already contains Markdown formatting)
"""

from __future__ import annotations

import sys
from pathlib import Path


def consolidate_ocr_output(hashdir: str, *, limit: int | None = None) -> tuple[str, str]:
    """Consolidate OCR outputs into book.txt and book.md.

    Args:
        hashdir: Output directory (e.g., output/a3f8c2d1e5b7f9c0).
        limit: Process only first N files (for testing).

    Returns:
        Tuple of (book_txt_path, book_md_path).
    """
    base_dir = Path(hashdir)
    ocr_output_dir = base_dir / "ocr_output"
    text_file = base_dir / "book.txt"
    md_file = base_dir / "book.md"

    if not ocr_output_dir.exists():
        raise FileNotFoundError(f"OCR output directory not found: {ocr_output_dir}")

    # Read OCR text files from ocr_texts/ directory
    ocr_texts_dir = ocr_output_dir / "ocr_texts"
    if not ocr_texts_dir.exists():
        raise FileNotFoundError(f"OCR texts directory not found: {ocr_texts_dir}")

    pages = sorted(ocr_texts_dir.glob("*.txt"))
    if limit:
        print(f"Processing first {limit} of {len(pages)} files", file=sys.stderr)
        pages = pages[:limit]

    if not pages:
        raise FileNotFoundError(f"No OCR output files found in: {ocr_texts_dir}")

    print(f"Consolidating {len(pages)} pages...")

    # Build book.txt and book.md
    # Layout-aware OCR already produces Markdown-formatted text
    # (## headings, ``` code fences, etc.)
    txt_lines: list[str] = []
    md_lines: list[str] = []

    for page_file in pages:
        page_name = page_file.stem
        page_text = page_file.read_text(encoding="utf-8").rstrip()

        # book.txt: plain text with page markers
        txt_lines.append(f"\n--- {page_name} ---\n\n")
        txt_lines.append(page_text)
        txt_lines.append("\n\n")

        # book.md: same content (already Markdown-formatted by layout_ocr)
        md_lines.append(f"\n--- {page_name} ---\n\n")
        md_lines.append(page_text)
        md_lines.append("\n\n")

    # Write files
    text_file.write_text("".join(txt_lines), encoding="utf-8")
    md_file.write_text("".join(md_lines), encoding="utf-8")

    print(f"  Created: {text_file}")
    print(f"  Created: {md_file}")

    return str(text_file), str(md_file)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Consolidate OCR outputs into book.txt and book.md")
    parser.add_argument(
        "hashdir",
        help="Output directory (e.g., output/a3f8c2d1e5b7f9c0)",
    )

    args = parser.parse_args()

    try:
        text_file, md_file = consolidate_ocr_output(hashdir=args.hashdir)
        print(f"\n  book.txt: {text_file}")
        print(f"  book.md:  {md_file}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
