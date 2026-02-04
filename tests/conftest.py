"""Shared pytest fixtures for video-separater tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def sample_image(tmp_path: Path) -> Path:
    """Create a simple test image and return its path."""
    img = Image.new("RGB", (100, 80), color=(200, 200, 200))
    path = tmp_path / "sample.png"
    img.save(path)
    return path


@pytest.fixture
def sample_pil_image() -> Image.Image:
    """Create a simple PIL Image for testing."""
    return Image.new("RGB", (100, 80), color=(200, 200, 200))


@pytest.fixture
def sample_layout() -> dict:
    """Create a sample layout dict for testing figure markers and masking."""
    return {
        "page_0001.png": {
            "figures": [
                {
                    "type": "FIGURE",
                    "bbox": [10, 20, 50, 60],
                    "confidence": 0.95,
                    "cropped_path": "figures/page_0001_fig_0.png",
                },
                {
                    "type": "TABLE",
                    "bbox": [60, 10, 90, 70],
                    "confidence": 0.85,
                    "cropped_path": "figures/page_0001_tab_0.png",
                },
            ]
        },
        "page_0002.png": {
            "figures": [
                {
                    "type": "FIGURE",
                    "bbox": [5, 5, 95, 75],
                    "confidence": 0.5,
                    "cropped_path": "figures/page_0002_fig_0.png",
                },
            ]
        },
    }
