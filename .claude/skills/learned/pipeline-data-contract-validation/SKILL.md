---
name: pipeline-data-contract-validation
description: "Validate data contracts between pipeline stages using real output during setup phase to prevent schema assumption failures"
---

# Pipeline Data Contract Validation

## Problem

When implementing features that consume data from earlier pipeline stages, it's easy to make **false assumptions about data schemas**. This leads to:

- Implementation based on incorrect assumptions
- All tests passing with mock data
- Complete failure in production/real pipeline
- Wasted implementation effort (4+ hours in this case)

**Specific Example**: Assumed `layout.json` contained `ocr_text` field, but actual yomitoku output only had `bbox`, `type`, `label`. Code detection feature was implemented and tested successfully with mocks, but failed completely in real pipeline.

## Solution

### 1. Setup Phase: Real Data Schema Validation (MANDATORY)

```markdown
# Task Definition Pattern
- [ ] T001 Identify upstream component (e.g., yomitoku)
- [ ] T001a **Run upstream component and capture actual output**
- [ ] T001b **Document all fields present in real output**
- [ ] T001c **Document all fields MISSING from real output**
- [ ] T001d **Validate assumptions against real schema**
```

**Action**: Run the actual pipeline step and inspect the output file:
```bash
# Example
python -m src.detect_layout --input samples/page.jpg --output /tmp/layout.json
cat /tmp/layout.json | jq '.regions[0]'  # Inspect actual fields
```

### 2. Document Data Flow with Field Availability

```markdown
# Improved Data Flow Diagram
[Image] → [yomitoku] → [layout.json]
                          ↓
                    ✅ fields: bbox, type, label
                    ❌ missing: ocr_text ← EXPLICIT!
                          ↓
                      [OCR execution]
                          ↓
                    ✅ fields: text content
                          ↓
                   [your_feature] ← Can use text here
```

### 3. Integration Tests: Real Pipeline Data Only

```python
# ❌ BAD: Mock data that doesn't match reality
def test_code_detection():
    layout = {"regions": [{"type": "TEXT", "ocr_text": "def foo(): pass"}]}
    result = detect_code(layout)  # Passes but wrong!

# ✅ GOOD: Use actual pipeline output
def test_code_detection():
    # Load actual yomitoku output
    with open("tests/fixtures/real_layout.json") as f:
        layout = json.load(f)
    result = detect_code(layout)  # Catches schema mismatch
```

### 4. Explicit Preconditions in Task Definitions

```markdown
# Task Definition with Preconditions
- [ ] T017 Implement detect_code_regions()
  - **Precondition**: layout.json contains `ocr_text` field
  - **Verification**: Confirmed in T001b
  - **If missing**: Adjust design to use alternative data source
```

## Example

### Before (Failure Case)

```python
# spec.md assumption
"Use ocr_text from layout.json regions"

# T001: Check yomitoku API
✓ Document function names
✓ Document processing flow
✗ Verify actual output schema  # SKIPPED!

# Implementation
def detect_code(layout):
    for region in layout["regions"]:
        text = region["ocr_text"]  # Field doesn't exist!
```

### After (Success Case)

```python
# T001a: Verify real schema
$ python -m src.detect_layout --input sample.jpg --output /tmp/layout.json
$ cat /tmp/layout.json
{
  "regions": [
    {"bbox": [...], "type": "TEXT", "label": "text"}
    # Note: NO ocr_text field!
  ]
}

# T001b: Update design
"ocr_text not available in layout.json
 → Must use rover/*.txt files from OCR step
 → Adjust implementation to read from correct source"
```

## When to Use

**Trigger this pattern when:**

1. Implementing features that consume data from **other pipeline stages**
2. **Setup Phase** of any spec-driven development workflow
3. Working with **external tools/libraries** where output format is uncertain
4. Designing **data transformations** between components

**Red Flags (use immediately):**

- ⚠️ "I assume this field exists in the output..."
- ⚠️ "The documentation says it should have..."
- ⚠️ "Let me create mock data with the fields I need..."
- ⚠️ Integration tests only use hand-crafted fixtures

**Prevention Checklist:**

- [ ] Have I run the actual upstream component?
- [ ] Have I inspected the real output file?
- [ ] Have I documented what fields are MISSING?
- [ ] Do my integration tests use real pipeline data?
- [ ] Are my preconditions explicitly stated in task definitions?

## Impact Metrics

**From Original Incident:**
- Time wasted: ~4 hours (Phase 1-6 implementation)
- Tests written: 55 (all passing with mocks)
- Root cause identification: 30 minutes
- Actual fix: 20-30 lines, ~1 hour

**With This Pattern:**
- Schema validation: 15-30 minutes in Setup Phase
- Wasted implementation: 0 hours
- False confidence: Eliminated
