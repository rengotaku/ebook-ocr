"""ROVER (Recognizer Output Voting Error Reduction) package.

This package provides OCR ensemble functionality combining multiple engines.

Modules:
- ensemble: ROVER merge algorithm
- engines: OCR engine wrappers
- alignment: Character-level text alignment
- output: Output directory management
"""

from src.rover import alignment, engines, ensemble, output

__all__ = ["ensemble", "engines", "alignment", "output"]
