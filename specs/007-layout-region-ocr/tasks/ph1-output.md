# Phase 1 Output: Setup Analysis

**Date**: 2026-02-11
**Phase**: Setup (Analysis Only)

## T001: src/detect_figures.py Analysis

### Current Implementation

```python
LABEL_TYPE_MAP = {
    "table": "TABLE",
    "figure": "FIGURE",
    "isolated formula": "FORMULA",
}
TARGET_LABELS = set(LABEL_TYPE_MAP.keys())  # Only 3 classes
```

### Required Changes

1. **Expand LABEL_TYPE_MAP** to 10 classes:
   ```python
   LABEL_TYPE_MAP = {
       "title": "TITLE",
       "plain text": "TEXT",
       "abandon": "ABANDON",
       "figure": "FIGURE",
       "figure_caption": "CAPTION",
       "table": "TABLE",
       "table_caption": "CAPTION",
       "table_footnote": "FOOTNOTE",
       "isolated formula": "FORMULA",
       "formula_caption": "CAPTION",
   }
   ```

2. **Change output structure**: `figures` → `regions` + add `page_size`

3. **Add min_area filtering**: Filter out small noise regions

### Key Integration Points

- Line 100: `layout_data[page_name] = {"figures": figures}` → Change to `regions`
- Need to capture `img.size` for `page_size` field

---

## T002: src/ocr_deepseek.py Analysis

### Current Implementation

- `ocr_page_deepseek()`: Single page OCR with optional pre-processed image
- `ocr_pages_deepseek()`: Batch OCR with figure masking via layout
- Uses `mask_figure_regions()` from utils to white-out figures before OCR

### Region OCR Integration Points

1. **Function Signature** (Line 81-88):
   ```python
   def ocr_page_deepseek(
       page_path: str,
       ...
       img: Image.Image | None = None,  # Can pass pre-cropped region
   )
   ```
   - Already supports passing a PIL Image directly (for cropped regions)

2. **Reusable for Region OCR**:
   - `ocr_page_deepseek()` can be called per-region with cropped image
   - No modification needed to this function

3. **New Module Needed**: `layout_ocr.py`
   - Orchestrates region-based OCR
   - Calls `ocr_page_deepseek()` for TEXT/TITLE regions
   - Calls VLM for FIGURE regions

---

## T003: src/utils.py Analysis

### Current Functions

| Function | Purpose | Status |
|----------|---------|--------|
| `encode_image_file()` | File to base64 | Reusable |
| `encode_pil_image()` | PIL Image to base64 | Reusable |
| `format_figure_markers()` | Generate figure markers | Update for `regions` |
| `mask_figure_regions()` | White-out figures | Update for `regions` |

### Required Addition

```python
def crop_region(img: Image.Image, bbox: list[int]) -> Image.Image:
    """Crop a region from image by bbox [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    return img.crop((x1, y1, x2, y2))
```

### Backward Compatibility Updates

`format_figure_markers()` and `mask_figure_regions()`:
- Need to support both `figures` (old) and `regions` (new) keys

---

## T004: tests/test_ocr_deepseek.py Analysis

### Test Patterns Identified

1. **Mock Pattern**: Uses `unittest.mock.patch` to mock Ollama API
2. **Fixture Pattern**: Uses `tmp_path` pytest fixture for test images
3. **Class Organization**: One class per logical test group
4. **Assertion Style**: Descriptive messages in assert statements

### Test Structure Template

```python
class TestFeatureName:
    """Description of test group."""

    def test_specific_behavior(self, tmp_path: Path) -> None:
        """What this test verifies."""
        # Arrange
        ...
        # Act
        ...
        # Assert
        assert result == expected, f"Expected ..., got {result}"
```

---

## Summary

| File | Changes Required |
|------|------------------|
| src/detect_figures.py | LABEL_TYPE_MAP expansion, regions structure, page_size, min_area |
| src/ocr_deepseek.py | No changes (reuse ocr_page_deepseek) |
| src/utils.py | Add crop_region(), update for regions key |
| src/layout_ocr.py | **New file**: region-based OCR dispatcher |
| src/reading_order.py | **New file**: reading order sort algorithm |

## Next Phase

Phase 2 will implement US1 (Extended Layout Detection) using TDD:
1. RED: Write tests for 10-class detection and regions structure
2. GREEN: Implement LABEL_TYPE_MAP expansion and output format change
