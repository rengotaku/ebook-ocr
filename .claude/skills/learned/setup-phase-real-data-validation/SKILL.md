---
name: setup-phase-real-data-validation
description: "Validate actual data output and schema during Setup Phase before implementation to prevent false assumptions"
---

# Setup Phase Real Data Validation

## Problem

During Setup Phase (T001), developers often document API signatures and processing flows but **skip verifying actual output**. This leads to:

- Assumptions about data schemas that don't match reality
- Implementation built on false premises
- Complete failure when integrated with real pipeline
- Wasted development time (4+ hours in documented case)

**Example**: Documented `layout.json` format without running yomitoku to see actual output. Assumed `ocr_text` field existed when it didn't.

## Solution

### Mandatory Setup Phase Tasks

```markdown
# Original (Insufficient)
- [X] T001 既存のレイアウト検出実装を確認
  - Document function names
  - Document processing flow

# Improved (Complete)
- [X] T001 既存のレイアウト検出実装を確認
  - Document function names
  - Document processing flow
- [ ] T001a **実際の出力を取得し、フィールドを検証**
  - Run actual component with sample input
  - Capture and inspect real output file
  - List ALL fields present
  - List ALL fields MISSING (especially expected ones)
- [ ] T001b **入力データの事前条件を明文化**
  - Document what fields ARE available
  - Document what fields are NOT available
  - Update spec if assumptions were wrong
```

### Step-by-Step Validation

**1. Run the component:**
```bash
# Example: Validate yomitoku output
python -m src.detect_layout \
  --input samples/page.jpg \
  --output /tmp/layout.json
```

**2. Inspect actual output:**
```bash
# Pretty-print and examine structure
cat /tmp/layout.json | jq '.regions[0]'

# Output:
# {
#   "bbox": [100, 200, 300, 400],
#   "type": "TEXT",
#   "label": "text"
#   # NOTE: No "ocr_text" field!
# }
```

**3. Document findings:**
```markdown
## T001a: Actual yomitoku Output Schema

**Fields Present**:
- `bbox`: [x1, y1, x2, y2]
- `type`: "TEXT" | "FIGURE" | "TABLE"
- `label`: string

**Fields MISSING**:
- ❌ `ocr_text` - NOT present in yomitoku output
- ❌ `confidence` - NOT present

**Conclusion**: Cannot use `ocr_text` from layout.json
→ Must adjust design to use rover/*.txt files instead
```

**4. Update spec if needed:**
If assumptions were wrong, stop and update `spec.md` before continuing implementation.

## Example

### Before (Failure)

```markdown
# T001: Check yomitoku implementation
- [X] Document function names: `detect_layout()`, `parse_regions()`
- [X] Document format: "layout.json with regions array"

# Proceed to implementation...
# (Never actually ran yomitoku to verify output)
```

**Result**: Implemented feature assuming `ocr_text` exists → Complete failure in real pipeline

### After (Success)

```markdown
# T001: Check yomitoku implementation
- [X] Document function names: `detect_layout()`, `parse_regions()`
- [X] Document format: "layout.json with regions array"

# T001a: Verify actual output
- [X] Run: `python -m src.detect_layout --input sample.jpg`
- [X] Inspect: layout.json contains only bbox, type, label
- [X] Verify: NO ocr_text field present
- [X] Document: Text content not available at this stage

# T001b: Update design
- [X] Adjust spec: Cannot use layout.json for text-based detection
- [X] Alternative: Use rover/*.txt files from OCR step
```

**Result**: Design corrected before implementation → Feature works in real pipeline

## When to Use

**Trigger this pattern when:**

1. **Setup Phase** of any feature implementation
2. Consuming data from **external components** (libraries, tools, other services)
3. Working with **file formats** you haven't personally generated yet
4. Implementing features based on **documentation** rather than real output

**Red Flags:**

- ⚠️ "The documentation says it outputs..."
- ⚠️ "I assume the output contains..."
- ⚠️ "Let me proceed based on the API signature..."
- ⚠️ Setup phase has no "run and verify" tasks

**Checklist:**

- [ ] Have I actually **run** the upstream component?
- [ ] Have I **inspected** the real output file?
- [ ] Have I documented what fields are **present**?
- [ ] Have I documented what fields are **missing**?
- [ ] Have I updated the spec if assumptions were wrong?

## Impact

**Time Investment**: 15-30 minutes in Setup Phase
**Time Saved**: 4+ hours of wasted implementation
**Confidence**: High certainty before coding starts
**Rework**: Zero (vs. complete reimplementation)
