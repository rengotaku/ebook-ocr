# Data Model: コードブロックタグ付け機能

**Date**: 2026-02-21
**Status**: Complete

## Entities

### Code (新規)

**Location**: `src/book_converter/models.py`

```python
@dataclass(frozen=True)
class Code:
    """コードブロック要素"""

    text: str                    # コード本体（改行・インデント保持）
    confidence: float = 1.0      # Guesslang判定確率
    read_aloud: bool = False     # TTS読み上げ（常にFalse）
```

**Relationships**:
- `SectionElement` Union型に追加
- `Section.elements` に含まれる

**Validation Rules**:
- `text`: 空文字列可（空のコードブロック）
- `confidence`: 0.0 <= x <= 1.0
- `read_aloud`: 常にFalse（TTS除外）

---

### CodeRegion (新規)

**Location**: `src/layout/code_detector.py`

```python
@dataclass(frozen=True)
class CodeRegion:
    """レイアウト検出結果のコード領域"""

    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2) xyxy形式
    confidence: float                 # Guesslang判定確率
    is_code: bool                     # コード判定結果
    ocr_text: str = ""               # OCR抽出テキスト（判定用）
```

**Validation Rules**:
- `bbox`: 全座標が非負、x1 < x2, y1 < y2
- `confidence`: 0.0 <= x <= 1.0
- `is_code`: True/False

---

### CodeDetectionResult (新規)

**Location**: `src/layout/code_detector.py`

```python
@dataclass(frozen=True)
class CodeDetectionResult:
    """コード検出結果（1画像分）"""

    regions: tuple[CodeRegion, ...]  # 検出されたコード領域
    image_path: str                   # 入力画像パス
    processing_time_ms: float = 0.0   # 処理時間（性能計測用）
```

---

## Modified Entities

### SectionElement (変更)

**Location**: `src/book_converter/models.py`

```python
# Before
SectionElement = Union[Heading, Paragraph, List, Figure]

# After
SectionElement = Union[Heading, Paragraph, List, Figure, Code]
```

---

### layout.json Region (変更)

**Format**: JSON (ファイル)

```json
{
  "type": "CODE",
  "label": "code",
  "bbox": [100, 200, 500, 400],
  "confidence": 0.87
}
```

**New Region Type**: `"CODE"` を追加

---

## State Transitions

### コード検出フロー

```
[画像] → [yomitoku] → [layout.json v1]
                            ↓
                    [code_detector]
                            ↓
                    [layout.json v2] (CODE領域追加)
                            ↓
                        [OCR]
                            ↓
                      [book.md]
                            ↓
                      [parser]
                            ↓
                    [Code dataclass]
                            ↓
                    [xml_builder]
                            ↓
                    [<code> XML]
```

### Region State

| State | Type | Trigger |
|-------|------|---------|
| TEXT | yomitoku検出 | 初期状態 |
| CODE | code_detector | IoU>0 && is_code |
| TEXT (維持) | code_detector | IoU=0 or !is_code |

---

## XML Output

### Code 要素

```xml
<code readAloud="false">
def hello():
    print("Hello, World!")
</code>
```

**Attributes**:
- `readAloud`: 常に `"false"`（TTS除外）

**Content**:
- 改行・インデント保持
- 特殊文字はXMLエスケープ (`<` → `&lt;`)
