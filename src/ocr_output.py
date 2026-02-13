"""OCR output management for ROVER ensemble.

Manages directory structure and file outputs for:
- Raw engine outputs (before ROVER processing)
- ROVER-processed outputs (after補完)
"""

from __future__ import annotations

from pathlib import Path


class ROVEROutput:
    """ROVER output directory manager."""

    def __init__(self, base_dir: str | Path):
        """Initialize output manager.

        Args:
            base_dir: Base directory for all OCR outputs.
        """
        self.base_dir = Path(base_dir)

    @property
    def raw_dir(self) -> Path:
        """Directory for raw engine outputs."""
        return self.base_dir / "raw"

    @property
    def rover_dir(self) -> Path:
        """Directory for ROVER-processed outputs."""
        return self.base_dir / "rover"

    def save_raw(self, engine: str, page: str, text: str) -> None:
        """Save raw engine output.

        Args:
            engine: Engine name (yomitoku, paddleocr, easyocr, tesseract).
            page: Page identifier (e.g., "page_001").
            text: OCR text result.
        """
        engine_dir = self.raw_dir / engine
        engine_dir.mkdir(parents=True, exist_ok=True)
        output_file = engine_dir / f"{page}.txt"
        output_file.write_text(text, encoding="utf-8")

    def save_rover(self, page: str, text: str) -> None:
        """Save ROVER-processed output.

        Args:
            page: Page identifier (e.g., "page_001").
            text: ROVER-補完ed text.
        """
        self.rover_dir.mkdir(parents=True, exist_ok=True)
        output_file = self.rover_dir / f"{page}.txt"
        output_file.write_text(text, encoding="utf-8")

    def get_raw_text(self, engine: str, page: str) -> str:
        """Read raw engine output.

        Args:
            engine: Engine name.
            page: Page identifier.

        Returns:
            Raw OCR text, or empty string if file doesn't exist.
        """
        file_path = self.raw_dir / engine / f"{page}.txt"
        return file_path.read_text(encoding="utf-8") if file_path.exists() else ""

    def get_rover_text(self, page: str) -> str:
        """Read ROVER-processed output.

        Args:
            page: Page identifier.

        Returns:
            ROVER text, or empty string if file doesn't exist.
        """
        file_path = self.rover_dir / f"{page}.txt"
        return file_path.read_text(encoding="utf-8") if file_path.exists() else ""
