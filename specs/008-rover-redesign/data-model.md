# Data Model: ROVER OCR再設計

**Date**: 2026-02-14 | **Branch**: `008-rover-redesign`

## Entity Relationship Diagram

```
Image (input)
    │
    ├──[yomitoku]──→ YomitokuResult
    │                   ├── paragraphs: list[Paragraph]
    │                   └── words: list[Word]
    │
    ├──[paddleocr]──→ PaddleResult
    │                   └── items: list[TextWithBox]
    │
    └──[easyocr]────→ EasyResult (with CLAHE preprocessing)
                        └── items: list[TextWithBox]
                                        │
                                        ▼
                              ┌─────────────────┐
                              │  Line Clustering │
                              │   (by y-coord)   │
                              └────────┬────────┘
                                       ▼
                              ┌─────────────────┐
                              │  Line Alignment  │
                              │  (cross-engine)  │
                              └────────┬────────┘
                                       ▼
                              ┌─────────────────┐
                              │ Character Voting │
                              │  + Confidence    │
                              │   Recalculation  │
                              └────────┬────────┘
                                       ▼
                              ┌─────────────────┐
                              │  Garbage Filter  │
                              └────────┬────────┘
                                       ▼
                                 ROVERResult
```

## Core Entities

### TextWithBox

認識されたテキスト断片（bbox + 信頼度付き）。

```python
@dataclass
class TextWithBox:
    """Text with bounding box and confidence."""
    text: str
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float  # 0.0 - 1.0
    engine: str  # "yomitoku" | "paddleocr" | "easyocr"

    @property
    def y_center(self) -> float:
        """Vertical center position for line alignment."""
        return (self.bbox[1] + self.bbox[3]) / 2.0

    @property
    def x_center(self) -> float:
        """Horizontal center position."""
        return (self.bbox[0] + self.bbox[2]) / 2.0
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | str | Yes | 認識されたテキスト |
| bbox | tuple[int, int, int, int] | Yes | バウンディングボックス (x1, y1, x2, y2) |
| confidence | float | Yes | 認識信頼度 (0.0-1.0) |
| engine | str | Yes | エンジン名 |

**Validation Rules:**
- `confidence` は 0.0 以上 1.0 以下
- `bbox` の x1 < x2, y1 < y2

---

### OCRLine

y座標でグループ化された1行分のテキスト。

```python
@dataclass
class OCRLine:
    """Single line of OCR result from one engine."""
    items: list[TextWithBox]
    engine: str
    y_center: float
    confidence: float  # 行全体の信頼度（最小値または平均値）

    @property
    def text(self) -> str:
        """Concatenated text from all items (sorted by x)."""
        sorted_items = sorted(self.items, key=lambda x: x.bbox[0])
        return "".join(item.text for item in sorted_items)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box covering all items."""
        if not self.items:
            return (0, 0, 0, 0)
        return (
            min(item.bbox[0] for item in self.items),
            min(item.bbox[1] for item in self.items),
            max(item.bbox[2] for item in self.items),
            max(item.bbox[3] for item in self.items),
        )
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | list[TextWithBox] | Yes | 行内のテキスト断片 |
| engine | str | Yes | エンジン名 |
| y_center | float | Yes | 行のy座標中心 |
| confidence | float | Yes | 行全体の信頼度 |

---

### AlignedLine

複数エンジンの結果がアライメントされた1行。

```python
@dataclass
class AlignedLine:
    """Aligned line from multiple engines."""
    lines: dict[str, OCRLine | None]  # engine -> line (None if missing)
    y_center: float
    voted_text: str = ""
    final_confidence: float = 0.0
    source_engines: list[str] = field(default_factory=list)
    is_garbage: bool = False
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| lines | dict[str, OCRLine \| None] | Yes | エンジン毎の行 |
| y_center | float | Yes | アライメント後のy座標 |
| voted_text | str | No | 投票結果テキスト |
| final_confidence | float | No | 再計算後の最終信頼度 |
| source_engines | list[str] | No | 採用されたエンジン |
| is_garbage | bool | No | ゴミ判定フラグ |

---

### AlignedPosition (NEW)

文字レベルでアライメントされた1つの位置。真のROVER投票の単位。

```python
@dataclass
class AlignedPosition:
    """Single position in character-level alignment."""
    position: int  # 基準テキストでの位置
    candidates: dict[str, str]  # engine -> character (None if gap)
    confidences: dict[str, float]  # engine -> confidence
    voted_char: str = ""
    vote_weight: float = 0.0

    def vote(self, engine_weights: dict[str, float]) -> str:
        """信頼度重み付き投票で最良の文字を選択"""
        votes: dict[str, float] = {}
        for engine, char in self.candidates.items():
            if char is None:
                continue
            weight = engine_weights.get(engine, 1.0) * self.confidences.get(engine, 0.5)
            votes[char] = votes.get(char, 0) + weight
        if not votes:
            return ""
        self.voted_char = max(votes, key=votes.get)
        self.vote_weight = votes[self.voted_char]
        return self.voted_char
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| position | int | Yes | 基準テキストでの位置 |
| candidates | dict[str, str] | Yes | エンジン毎の候補文字 |
| confidences | dict[str, float] | Yes | エンジン毎の信頼度 |
| voted_char | str | No | 投票結果の文字 |
| vote_weight | float | No | 採用された文字の重み |

---

### ROVERResult

ROVER処理の最終結果。

```python
@dataclass
class ROVERResult:
    """ROVER processing result."""
    text: str
    lines: list[str]
    aligned: list[AlignedLine]
    engine_contributions: dict[str, int]
    gaps_filled: int = 0
    garbage_filtered: int = 0
    statistics: dict[str, any] = field(default_factory=dict)
```

**Fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | str | Yes | 最終テキスト（改行区切り） |
| lines | list[str] | Yes | 行単位のテキスト |
| aligned | list[AlignedLine] | Yes | アライメント結果 |
| engine_contributions | dict[str, int] | Yes | エンジン毎の貢献行数 |
| gaps_filled | int | No | 補完された行数 |
| garbage_filtered | int | No | フィルタされたゴミ行数 |
| statistics | dict | No | 追加統計情報 |

---

### EngineResult

単一エンジンの処理結果。

```python
@dataclass
class EngineResult:
    """Result from a single OCR engine."""
    engine: str
    items: list[TextWithBox]
    success: bool
    error: str | None = None
    raw_text: str = ""  # 生のテキスト出力

    @property
    def text(self) -> str:
        """Concatenated text from all items."""
        return "\n".join(item.text for item in self.items)
```

---

## State Transitions (True ROVER)

```
[Image Input]
     │
     ▼
[OCR Processing] ─────────────────────┐
     │                                │
     ├── yomitoku → EngineResult      │
     ├── paddleocr → EngineResult     │  並列実行可能
     └── easyocr (CLAHE) → EngineResult│
                                      │
     ▼◄────────────────────────────────┘
[Garbage Filter]  ← 投票前に実行
     │
     │  - confidence < 0.5 を除外
     │  - 日本語なし短文を除外
     │  - 繰り返し文字を除外
     │
     ▼
[Line Clustering]
     │
     │  各エンジンの items を y座標でグループ化
     │  → dict[str, list[OCRLine]]
     │
     ▼
[Line Alignment]
     │
     │  y座標が近い行を cross-engine でマッチ
     │  → list[AlignedLine]
     │
     ▼
[Character-Level Alignment]  ← NEW: 真のROVER
     │
     │  difflib.SequenceMatcher で文字単位アライメント
     │  → list[AlignedPosition]
     │
     ▼
[Weighted Voting]  ← NEW: 信頼度重み付き多数決
     │
     │  各文字位置で:
     │    weight = engine_weight * confidence
     │    votes[char] += weight
     │  → 最高得票の文字を採用
     │
     ▼
[ROVERResult]
```

---

## Validation Rules Summary

| Entity | Rule | Error |
|--------|------|-------|
| TextWithBox.confidence | 0.0 ≤ value ≤ 1.0 | ValueError |
| TextWithBox.bbox | x1 < x2, y1 < y2 | ValueError |
| OCRLine.items | len > 0 | Empty line |
| AlignedLine.lines | at least one non-None | Skip line |
| ROVERResult | - | Always valid |

---

## Engine-Specific Notes

### yomitoku

```python
# paragraphs + words 併用
results.paragraphs  # 構造情報（box, contents, order, role）
results.words       # 信頼度情報（content, rec_score, points）

# paragraph の信頼度計算
def get_paragraph_confidence(paragraph, words):
    """paragraphに含まれるwordsのrec_scoreの最小値"""
    ...
```

### PaddleOCR

```python
# PaddleOCR 3.x API
result = reader.predict(img_array)
# result[0]: {"rec_texts": [...], "rec_scores": [...], "rec_polys": [...]}
```

### EasyOCR

```python
# CLAHE前処理後に実行
preprocessed = apply_clahe(image)
results = reader.readtext(preprocessed, detail=1)
# results: [(bbox_points, text, confidence), ...]
```
