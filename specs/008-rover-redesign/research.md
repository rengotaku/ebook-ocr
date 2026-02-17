# Research: ROVER OCR再設計

**Date**: 2026-02-14 | **Branch**: `008-rover-redesign`

## 1. yomitoku `paragraphs` + `words` 併用

### Decision
`results.paragraphs` で構造・順序を取得し、`results.words` で信頼度（`rec_score`）を取得する。

### Rationale
- `DocumentAnalyzerSchema` は `paragraphs`, `tables`, `words`, `figures` の4フィールドを持つ
- `ParagraphSchema`: `box`, `contents`, `direction`, `order`, `role`（信頼度なし）
- `WordPrediction`: `points`, `content`, `direction`, `rec_score`, `det_score`（信頼度あり）
- 信頼度が必要なのは投票時のみ。構造情報は`paragraphs`から取得可能。

### Implementation Pattern

```python
from yomitoku import DocumentAnalyzer

analyzer = DocumentAnalyzer(visualize=False, device="cpu")
results, _, _ = analyzer(cv_img)

# 構造情報: paragraphs
for p in results.paragraphs:
    text = p.contents
    bbox = p.box  # [x1, y1, x2, y2]
    order = p.order
    role = p.role  # "section_headings" or None

# 信頼度: words
word_confidences = {}
for w in results.words:
    word_confidences[w.content] = {
        "rec_score": w.rec_score,  # 認識信頼度
        "det_score": w.det_score,  # 検出信頼度
        "points": w.points,        # ポリゴン座標
    }
```

### Paragraph → Word マッチング戦略

座標ベースマッチング:
```python
def get_paragraph_confidence(paragraph, words):
    """paragraphに含まれるwordsのrec_scoreの最小値を返す"""
    p_box = paragraph.box  # [x1, y1, x2, y2]
    contained_words = []

    for word in words:
        # word.points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        w_center = word_center(word.points)
        if point_in_box(w_center, p_box):
            contained_words.append(word.rec_score)

    return min(contained_words) if contained_words else 0.0
```

### Alternatives Considered
1. **paragraphsのみ使用（現状）** - 信頼度が取得できず却下
2. **wordsのみ使用** - 構造情報が失われるため却下
3. **テキストマッチングでword検索** - 重複テキストで曖昧になるため却下

---

## 2. 真のROVERアルゴリズム（文字レベル投票）

### Decision
音声認識分野のROVER (Recognizer Output Voting Error Reduction) に準拠し、文字レベルでのアライメントと**信頼度重み付き多数決投票**を行う。

### Rationale
- 単純な `max(conf)` では投票ではなくフィルタリングに過ぎない
- 本来のROVERは各位置で多数決を行い、信頼度を投票の重みとして使用
- 「ソフトウェア」vs「ソフトウエア」問題を正しく解決できる

### アルゴリズム概要

1. **行レベルアライメント**: y座標でエンジン間の行をマッチング
2. **文字レベルアライメント**: `difflib.SequenceMatcher` で文字単位アライメント
3. **信頼度重み付き投票**: 各位置で `weight = engine_weight * confidence` による多数決
4. **ゴミフィルタ**: 投票前に低信頼度テキストを除外

### Implementation Pattern

```python
from difflib import SequenceMatcher
import unicodedata

ENGINE_WEIGHTS = {"yomitoku": 1.5, "paddleocr": 1.2, "easyocr": 1.0}

def normalize_text(text: str) -> str:
    """NFKC正規化 + 空白正規化"""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'[\s　]+', ' ', text)
    return text.strip()

def align_texts(texts: list[str]) -> list[dict[int, str]]:
    """複数テキストを文字レベルでアライメント"""
    if len(texts) < 2:
        return [{i: c for i, c in enumerate(texts[0])}] if texts else []

    # 基準テキスト（最長）に他をアライメント
    base = max(texts, key=len)
    aligned = []

    for text in texts:
        matcher = SequenceMatcher(None, normalize_text(base), normalize_text(text))
        char_map = {}
        for block in matcher.get_matching_blocks():
            for i in range(block.size):
                char_map[block.a + i] = text[block.b + i] if block.b + i < len(text) else None
        aligned.append(char_map)

    return aligned

def weighted_vote(
    candidates: dict[str, str],  # engine -> char
    confidences: dict[str, float],  # engine -> confidence
) -> tuple[str, float]:
    """信頼度重み付き投票で最良の文字を選択"""
    votes: dict[str, float] = {}

    for engine, char in candidates.items():
        if char is None:
            continue
        weight = ENGINE_WEIGHTS.get(engine, 1.0) * confidences.get(engine, 0.5)
        votes[char] = votes.get(char, 0) + weight

    if not votes:
        return "", 0.0

    best_char = max(votes, key=votes.get)
    total_weight = sum(votes.values())
    confidence = votes[best_char] / total_weight if total_weight > 0 else 0.0

    return best_char, confidence
```

### 例: 「ソフトウェア」vs「ソフトウエア」

| 位置 | yomitoku (w=1.5, c=0.9) | paddle (w=1.2, c=0.95) | easy (w=1.0, c=0.7) | 投票結果 |
|------|------------------------|------------------------|---------------------|----------|
| 4 | **ェ** | **エ** | **ェ** | **ェ** (1.35 + 0.7 = 2.05 > 1.14) |

→ 多数派の「ソフトウェア」が採用される

### Alternatives Considered
1. **max(conf)のみ** - 投票ではなくフィルタリング、部分誤り修正不可 → 却下
2. **単純多数決（重みなし）** - 高品質エンジンの優位性が失われる → 却下
3. **Levenshtein距離** - difflib.SequenceMatcherで十分 → 却下

---

## 3. CLAHE前処理

### Decision
EasyOCRのみにCLAHE（Contrast Limited Adaptive Histogram Equalization）を適用する。

### Rationale
- yomitoku/PaddleOCR: 内部前処理が充実（向き検出、歪み補正、レイアウト解析）
- EasyOCR: 基本的な前処理のみ。低品質画像に弱い
- Tesseract: 除外決定済み

### Implementation

```python
import cv2
import numpy as np

def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8) -> np.ndarray:
    """Apply CLAHE preprocessing for EasyOCR.

    Args:
        image: RGB image array (H, W, 3)
        clip_limit: Threshold for contrast limiting
        tile_size: Size of grid for histogram equalization

    Returns:
        Preprocessed RGB image
    """
    # Convert RGB to LAB
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])

    # Convert back to RGB
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
```

### パラメータ

| パラメータ | 値 | 理由 |
|-----------|-----|------|
| clip_limit | 2.0 | デフォルト値、ほとんどの画像で効果的 |
| tile_size | 8 | 標準的なグリッドサイズ、計算コストとのバランス |

### Alternatives Considered
1. **全エンジンにCLAHE適用** - yomitoku/PaddleOCRの内部処理と干渉する可能性があるため却下
2. **適応的二値化** - 日本語書籍のカラー画像では効果が限定的
3. **前処理なし** - EasyOCRの精度が低下するため却下

---

## 4. ゴミフィルタ

### Decision
以下の条件でゴミ出力を除外:
1. 信頼度 < 0.5
2. 日本語文字を含まない短い文字列（5文字以下のASCII）
3. 同一文字が5回以上繰り返し

### Implementation

```python
import re

def is_garbage(text: str, confidence: float, min_confidence: float = 0.5) -> bool:
    """ゴミ出力かどうかを判定"""
    # 空テキスト
    if not text.strip():
        return True

    # 信頼度が低い
    if confidence < min_confidence:
        return True

    # 日本語を含まない短いASCII
    has_japanese = bool(re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]', text))
    if not has_japanese and len(text) <= 5:
        return True

    # 同一文字の繰り返し（5回以上）
    if re.search(r'(.)\1{4,}', text):
        return True

    return False
```

### Alternatives Considered
1. **LLMによる幻覚検出** - 処理時間が長すぎるため却下
2. **辞書ベース検証** - メンテナンスコストが高いため却下
3. **単純な長さフィルタのみ** - 誤検出が多いため却下

---

## Summary

| 項目 | 決定 |
|------|------|
| yomitoku構造 | `paragraphs` + `words` 併用、座標マッチング |
| アライメント | `difflib.SequenceMatcher` で文字レベルアライメント |
| 投票方式 | **信頼度重み付き多数決** (`weight = engine_weight * confidence`) |
| 前処理 | EasyOCRのみCLAHE（clip=2.0, tile=8） |
| ゴミフィルタ | conf<0.5、日本語なしASCII、繰り返し文字 |
