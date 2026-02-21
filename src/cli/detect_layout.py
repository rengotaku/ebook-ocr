"""CLI wrapper for detect_layout."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.layout.code_detector import detect_code_regions
from src.layout.detector import detect_layout


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Detect page layout")
    parser.add_argument("pages_dir", help="Pages directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device to use (default: cpu)",
    )
    parser.add_argument(
        "--detect-code",
        action="store_true",
        help="Enable code block detection",
    )
    parser.add_argument(
        "--code-threshold",
        type=float,
        default=0.6,
        help="Code detection confidence threshold (default: 0.6)",
    )
    args = parser.parse_args()

    # Validate input
    if not Path(args.pages_dir).exists():
        print(f"Error: Input not found: {args.pages_dir}", file=sys.stderr)
        return 1

    # Call existing function
    try:
        layout_data = detect_layout(args.pages_dir, args.output, device=args.device)

        # Apply code detection if enabled
        if args.detect_code:
            print("\n=== Code Block Detection ===")
            code_count = 0
            for page_name, page_layout in layout_data.items():
                updated = detect_code_regions(page_layout, threshold=args.code_threshold)
                layout_data[page_name] = updated
                page_codes = sum(1 for r in updated["regions"] if r["type"] == "CODE")
                if page_codes:
                    print(f"  {page_name}: {page_codes} code block(s) detected")
                    code_count += page_codes

            # Re-save layout.json with CODE regions
            layout_file = Path(args.output) / "layout.json"
            with open(layout_file, "w", encoding="utf-8") as f:
                json.dump(layout_data, f, indent=2, ensure_ascii=False)
            print(f"\nCode detection complete: {code_count} total code blocks")

        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
