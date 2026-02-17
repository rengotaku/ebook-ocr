"""Consolidate ROVER outputs into book.txt and book.md.

This script combines individual page OCR results from ROVER into:
- book.txt: Plain text with page markers
- book.md: Markdown with heading formatting (## prefix)
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.ocr_output import ROVEROutput


def consolidate_rover_output(hashdir: str) -> tuple[str, str]:
    """Consolidate ROVER outputs into book.txt and book.md.

    Args:
        hashdir: Output directory (e.g., output/a3f8c2d1e5b7f9c0).

    Returns:
        Tuple of (book_txt_path, book_md_path).
    """
    base_dir = Path(hashdir)
    ocr_output_dir = base_dir / "ocr_output"
    text_file = base_dir / "book.txt"
    md_file = base_dir / "book.md"

    if not ocr_output_dir.exists():
        raise FileNotFoundError(f"OCR output directory not found: {ocr_output_dir}")

    # Load headings metadata
    rover_output = ROVEROutput(str(ocr_output_dir))
    all_headings = rover_output.get_all_headings()

    # Consolidate ROVER results
    rover_dir = ocr_output_dir / "rover"
    rover_pages = sorted(rover_dir.glob("*.txt"))

    if not rover_pages:
        raise FileNotFoundError(f"No ROVER output files found in: {rover_dir}")

    print(f"Consolidating {len(rover_pages)} pages...")
    print(f"  Headings: {len(all_headings)} pages with section headings")

    # Build book.txt (plain text, no heading markers)
    txt_lines: list[str] = []
    # Build book.md (with ## heading markers)
    md_lines: list[str] = []

    for page_file in rover_pages:
        page_name = page_file.stem
        page_headings = set(all_headings.get(page_name, []))
        page_text = page_file.read_text(encoding="utf-8")

        # book.txt: plain text
        txt_lines.append(f"\n--- {page_name} ---\n\n")
        txt_lines.append(page_text)
        txt_lines.append("\n\n")

        # book.md: apply heading markers
        if page_headings:
            lines = page_text.split("\n")
            new_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped in page_headings:
                    new_lines.append(f"\n## {stripped}\n")
                else:
                    new_lines.append(line)
            page_text = "\n".join(new_lines)

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
    parser = argparse.ArgumentParser(
        description="Consolidate ROVER outputs into book.txt and book.md"
    )
    parser.add_argument(
        "hashdir",
        help="Output directory (e.g., output/a3f8c2d1e5b7f9c0)",
    )

    args = parser.parse_args()

    try:
        text_file, md_file = consolidate_rover_output(hashdir=args.hashdir)
        print(f"\n✅ Consolidation complete")
        print(f"  book.txt: {text_file}")
        print(f"  book.md:  {md_file}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
