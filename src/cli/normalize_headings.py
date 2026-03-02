"""CLI entry point for heading normalization.

Provides subcommands:
- report: heading pattern analysis report
- normalize: normalize headings (dry-run or apply)
- validate: TOC-body heading validation report
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    """CLI entry point."""
    raise NotImplementedError("CLI normalize_headings is not yet implemented")


if __name__ == "__main__":
    sys.exit(main())
