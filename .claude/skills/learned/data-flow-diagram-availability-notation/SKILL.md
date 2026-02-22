---
name: data-flow-diagram-availability-notation
description: "Document data availability at each pipeline stage in flow diagrams to make dependencies and contradictions visible"
---

# Data Flow Diagram Availability Notation

## Problem

Traditional data flow diagrams show **processing order** but not **data availability**:

- Diagram shows step A → step B is correct order
- But doesn't show whether step B has the data it needs
- Contradictions exist but remain invisible
- Reviewers approve diagrams that contain impossible flows

**Example**: Diagram showed `[yomitoku] → [code_detector] → [OCR]` which is correct processing order, but code_detector **requires text** which isn't available until OCR runs. The diagram was accurate but incomplete.

## Solution

### Add Data Availability Annotations to Flow Diagrams

**Original Diagram (Processing Order Only)**:
```
[yomitoku] → [layout.json v1]
                   ↓
           [code_detector] ← NEW
                   ↓
             [book.md via OCR]
```

**Problem**: Diagram is **accurate** but doesn't reveal the contradiction. We can't see that code_detector needs text that doesn't exist yet.

**Improved Diagram A (Data Availability Inline)**:
```
[yomitoku] → [layout.json]
                  │
                  │ ✅ fields: bbox, type, label
                  │ ❌ missing: text content ← EXPLICIT
                  ↓
           [code_detector]
                  │
                  │ 📋 requires: text content ← EXPLICIT
                  │ ⚠️  ERROR: not available! ← CONTRADICTION VISIBLE
```

**Improved Diagram B (Dependency Table)**:

| Step | Input | Output | Available Data | Required Data | Status |
|------|-------|--------|---------------|---------------|--------|
| yomitoku | image | layout.json | bbox, type, label | - | ✅ OK |
| code_detector | layout.json | CODE regions | bbox only | **text** | ❌ **text はどこから？** |
| OCR | image + layout | rover/*.txt | **text content** | - | ✅ OK |

→ Table format makes "where does text come from?" question immediately obvious

### Notation Guidelines

**Use symbols to show data state:**
- ✅ Data available at this stage
- ❌ Data NOT available (especially if expected)
- 📋 Data required by this step
- ⚠️ Contradiction/missing dependency

**Include for each stage:**
1. What data is **produced**
2. What data is **available** (cumulative)
3. What data is **required**
4. What data is **missing** (gap analysis)

## Example

### Before (Hidden Contradiction)

```markdown
## データフロー

[画像入力]
    ↓
[yomitoku] → layout.json 生成
    ↓
[コード検出] → CODE領域をマーキング
    ↓
[OCR実行] → テキスト抽出
    ↓
[Markdown生成]
```

**Review feedback**: "図は正確です。承認。"
**Result**: Implementation fails because code detection has no text

### After (Visible Contradiction)

```markdown
## データフロー（データ可用性つき）

[画像入力]
    ↓
[yomitoku] → layout.json 生成
    │
    │ ✅ Available: bbox, type, label
    │ ❌ Missing: text, confidence
    ↓
[コード検出] ← 📋 Requires: text content
    │         ⚠️ ERROR: text not available!
    │
    │ ❌ Cannot proceed (dependency unmet)
    ↓
[OCR実行] → テキスト抽出
    │
    │ ✅ Available: text content (NOW available)
    ↓
[コード検出] ← Can only run AFTER OCR
    ↓
[Markdown生成]
```

**Review feedback**: "⚠️ コード検出はテキストが必要だが、OCRの前に実行されています。設計を修正してください。"
**Result**: Design fixed before implementation

### Dependency Table Format

```markdown
## パイプライン依存関係

| Stage | Input Files | Output Files | Data Available | Data Required | Issues |
|-------|-------------|--------------|----------------|---------------|--------|
| 1. yomitoku | page.jpg | layout.json | bbox, type, label | - | - |
| 2. code_detect | layout.json | layout_v2.json | bbox, type, label | **text** | ❌ text not in layout.json |
| 3. OCR | page.jpg + layout.json | rover/*.txt | text content | - | - |
| 4. convert | rover/*.txt + layout.json | book.md | text + bbox | - | ✅ All available |

**矛盾**: Stage 2 requires `text` but it's not available until Stage 3.

**解決策**: Move code detection to Stage 4 (after OCR) or integrate into converter.
```

## When to Use

**Trigger this pattern when:**

1. Designing **multi-stage pipelines** with data dependencies
2. Adding **new processing steps** to existing pipeline
3. Reviewing **implementation plans** during Setup Phase
4. Creating **architecture documentation**

**Red Flags:**

- ⚠️ Diagram shows only boxes and arrows
- ⚠️ No mention of what data each stage produces/consumes
- ⚠️ Reviewer approves diagram without questioning dependencies
- ⚠️ "The diagram is correct" but implementation fails

**Questions to Ask:**

- What data **enters** this stage?
- What data **exists** at this stage?
- What data **leaves** this stage?
- What data is **required** but **missing**?

## Checklist

- [ ] Does diagram show **processing order**? ✓
- [ ] Does diagram show **data produced** at each stage?
- [ ] Does diagram show **data required** by each stage?
- [ ] Does diagram show **data available** (cumulative)?
- [ ] Does diagram show **missing data** explicitly?
- [ ] Are contradictions **visible** in the diagram?
- [ ] Can reviewer spot dependency issues from diagram alone?

## Impact

**Without Data Availability**:
- Diagram approved as "correct"
- Implementation proceeds
- Failure discovered after 4+ hours
- Complete redesign required

**With Data Availability**:
- Contradiction visible in diagram
- Reviewer spots issue immediately
- Design fixed before implementation
- Zero wasted development time

**Conclusion**: 図を書かないのではなく、**図の粒度**が問題。処理順序だけでなくデータ依存関係を含めることで矛盾が可視化される。
