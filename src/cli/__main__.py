"""Make src.cli package executable."""

import sys

print("Available CLI commands:", file=sys.stderr)
print("  python -m src.cli.extract_frames", file=sys.stderr)
print("  python -m src.cli.deduplicate", file=sys.stderr)
print("  python -m src.cli.split_spreads", file=sys.stderr)
print("  python -m src.cli.detect_layout", file=sys.stderr)
print("  python -m src.cli.run_ocr", file=sys.stderr)
print("  python -m src.cli.consolidate", file=sys.stderr)
sys.exit(1)
