---
name: integration-test-real-pipeline-data
description: "Use real pipeline output in integration tests instead of mocks to catch schema mismatches early"
---

# Integration Test Real Pipeline Data

## Problem

Integration tests that use **hand-crafted mock data** instead of real pipeline output create **false confidence**:

- All tests pass with mocks
- Real pipeline has different schema
- Feature completely fails in production
- No early warning of schema mismatches

**Example**: 55 integration tests passed using mock data with `ocr_text` field. Real yomitoku output had no such field → Complete failure in real pipeline.

## Solution

### Prohibit Mocks in Integration Tests

```markdown
# Original (Dangerous)
- [ ] T047 パイプライン統合テスト
  - Create test data
  - Verify code detection works

# Improved (Safe)
- [ ] T047 パイプライン統合テスト
  - **実際の yomitoku 出力を使用**
  - **モックデータ禁止**
  - **Step 1-6 の結合テスト**
  - Verify with real pipeline end-to-end
```

### Test Data Sources

```python
# ❌ BAD: Hand-crafted mock (schema drift)
def test_code_detection():
    layout = {
        "regions": [
            {"type": "TEXT", "ocr_text": "def hello(): pass"}
        ]
    }
    result = detect_code(layout)
    assert len(result) == 1  # Passes but wrong!

# ✅ GOOD: Real pipeline fixture
def test_code_detection():
    # Use actual yomitoku output as fixture
    with open("tests/fixtures/real_yomitoku_output.json") as f:
        layout = json.load(f)

    result = detect_code(layout)
    # Test fails immediately: KeyError: 'ocr_text'
    # → Catches schema mismatch early!
```

### Creating Real Fixtures

**Step 1: Generate fixture from actual pipeline**
```bash
# Run real pipeline step
python -m src.detect_layout \
  --input tests/samples/page_with_code.jpg \
  --output tests/fixtures/real_yomitoku_output.json

# Verify it's real output (not hand-edited)
git add tests/fixtures/real_yomitoku_output.json
```

**Step 2: Use fixture in tests**
```python
# tests/test_integration.py
import pytest
import json
from pathlib import Path

@pytest.fixture
def real_layout_output():
    """Load actual yomitoku output (not mock)."""
    fixture_path = Path(__file__).parent / "fixtures" / "real_yomitoku_output.json"
    with open(fixture_path) as f:
        return json.load(f)

def test_code_detection_with_real_data(real_layout_output):
    """Integration test using real pipeline data."""
    result = detect_code(real_layout_output)
    # If schema changed, this fails immediately
    assert result is not None
```

**Step 3: Document fixture provenance**
```markdown
# tests/fixtures/README.md

## Fixture Generation

All fixtures are generated from **real pipeline output**, not hand-crafted.

### real_yomitoku_output.json
- Generated: 2026-02-22
- Command: `python -m src.detect_layout --input samples/page_with_code.jpg`
- Purpose: Integration test for code detection
- Schema: yomitoku v0.10.0 output format

**DO NOT hand-edit this file.** Regenerate if pipeline changes.
```

## Example

### Before (False Confidence)

```python
# tests/test_code_detection.py
def test_detect_code_in_text_regions():
    # Hand-crafted mock with assumed schema
    layout = {
        "regions": [
            {
                "type": "TEXT",
                "bbox": [100, 200, 300, 400],
                "ocr_text": "def hello():\n    print('world')"  # Field doesn't exist!
            }
        ]
    }

    result = detect_code_regions(layout)
    assert len(result) == 1
    assert result[0]["type"] == "CODE"

# Test Output: PASS ✓ (55 tests pass)
# Real Pipeline: FAIL ✗ (KeyError: 'ocr_text')
```

### After (Early Detection)

```python
# tests/test_code_detection.py
import pytest
import json

@pytest.fixture
def real_yomitoku_output():
    with open("tests/fixtures/real_yomitoku_output.json") as f:
        return json.load(f)

def test_detect_code_in_text_regions(real_yomitoku_output):
    # Use real pipeline output
    result = detect_code_regions(real_yomitoku_output)

    # Test Output: FAIL ✗ (KeyError: 'ocr_text')
    # → Caught during development!
    # → Fix design before wasting 4 hours
```

## When to Use

**Trigger this pattern for:**

1. **Integration tests** (unit tests can use mocks)
2. Tests validating **pipeline stages** interact correctly
3. Tests verifying **data transformations** between components
4. **E2E tests** (absolutely must use real data)

**Red Flags:**

- ⚠️ Integration test creates its own test data
- ⚠️ "Let me just mock this for the test..."
- ⚠️ Test data has fields the real output doesn't
- ⚠️ All tests pass but pipeline fails

**Checklist:**

- [ ] Are my integration tests using **real pipeline output**?
- [ ] Do I have fixtures generated from **actual components**?
- [ ] Is fixture generation **documented** and **reproducible**?
- [ ] Do I **prohibit hand-editing** fixture files?
- [ ] Do I **regenerate fixtures** when pipeline changes?

## Guidelines

### When Mocks Are OK

- **Unit tests** - Testing single function in isolation
- **External APIs** - Can't run real API in tests
- **Slow operations** - Database queries, network calls

### When Mocks Are BANNED

- **Integration tests** - Testing component interactions
- **Data transformations** - Testing schema compatibility
- **Pipeline stages** - Testing end-to-end flow
- **File format parsing** - Testing real file structures

## Impact

**Documented Case:**
- Tests with mocks: 55 tests pass ✓
- Real pipeline: Complete failure ✗
- Wasted effort: 4+ hours implementation
- Detection time: After Phase 1-6 complete

**With Real Data:**
- First test run: Immediate failure ✗
- Detection time: During development
- Wasted effort: 0 hours
- Fix: Adjust design before implementation
