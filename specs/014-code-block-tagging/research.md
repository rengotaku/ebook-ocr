# Research: コードブロックタグ付け機能

**Date**: 2026-02-21
**Status**: Complete

## 1. Guesslang API Usage

### Decision
Guesslang `Guess` クラスを使用し、`language_name()` + `scores()` で判定。

### API パターン

```python
from guesslang import Guess

guess = Guess()

# 基本判定
language = guess.language_name(source_code)  # "Python" or None

# 確率取得
scores = guess.scores(source_code)  # {"Python": 0.98, "C": 0.01, ...}

# 確率ランキング
probs = guess.probabilities(source_code)  # [("Python", 0.98), ("C", 0.01), ...]
```

### 判定ロジック

```python
def is_code(text: str, threshold: float = 0.5) -> tuple[bool, float]:
    """コード判定（spec準拠）"""
    guess = Guess()
    language = guess.language_name(text)

    if language is None:
        return False, 0.0

    scores = guess.scores(text)
    confidence = scores.get(language, 0.0)

    return confidence >= threshold, confidence
```

### 推奨閾値

| 閾値 | 用途 |
|------|------|
| 0.8 | 高精度（誤検出最小化） |
| 0.5-0.6 | バランス（推奨） |
| 0.3-0.4 | 高再現率（取りこぼし最小化） |

**Rationale**: SC-005（誤検出率≤5%）を考慮し、初期値は0.6を推奨。

### Alternatives Considered

| 選択肢 | 却下理由 |
|--------|---------|
| Linguist (GitHub) | Ruby依存、API呼び出し複雑 |
| pygments | 言語検出より構文ハイライト向け |
| カスタムML | 学習データ・工数が必要 |

---

## 2. OpenCV 枠線検出

### Decision
Canny Edge Detection + `findContours` + `approxPolyDP` で4角形検出。

### 検出パイプライン

```python
import cv2
import numpy as np

def detect_bordered_rectangles(image_path: str) -> list[dict]:
    """枠線で囲まれた矩形領域を検出"""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]

    # 1. 前処理
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)

    # 2. モルフォロジー（枠線の途切れを補完）
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # 3. 輪郭検出
    contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for contour in contours:
        # 4角形に近似
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        if len(approx) != 4:
            continue

        x, y, w_rect, h_rect = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # フィルタリング
        if not _is_valid_code_block(area, w_rect, h_rect, h * w):
            continue

        rectangles.append({
            "bbox": [x, y, x + w_rect, y + h_rect],  # xyxy形式
            "area": area,
            "confidence": _calculate_confidence(contour)
        })

    return rectangles
```

### フィルタリング基準

| メトリクス | 最小値 | 最大値 | 根拠 |
|-----------|--------|--------|------|
| 面積比 | 0.5% | 75% | コードブロックの妥当なサイズ |
| アスペクト比 | 0.4 | 2.5 | 横長・縦長どちらも許容 |
| Solidity | 0.80 | 1.0 | 枠内が塗りつぶされている |
| Extent | 0.65 | 1.0 | バウンディングボックスを満たす |

### Canny パラメータ

```python
# 推奨設定（書籍画像向け）
CANNY_LOW = 50
CANNY_HIGH = 150  # 比率 3:1
GAUSSIAN_KERNEL = (5, 5)
MORPH_KERNEL = (5, 5)
```

### Alternatives Considered

| 選択肢 | 却下理由 |
|--------|---------|
| Hough Transform | 直線検出向け、矩形検出に不向き |
| YOLO/DocLayout | "code"クラスなし、学習必要 |
| Template Matching | 枠線スタイルが固定でない |

---

## 3. IoU 計算とマージ

### Decision
IoU > 0 で重複判定、TEXT領域をCODEで置換。

### IoU 計算

```python
def calculate_iou(box1: list, box2: list) -> float:
    """IoU (Intersection over Union) を計算"""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0
```

### マージロジック

```python
def merge_code_regions(layout: dict, code_regions: list) -> dict:
    """layout.jsonにコード領域をマージ"""
    updated_regions = []

    for region in layout["regions"]:
        # TEXT領域のみ置換対象
        if region["type"] != "TEXT":
            updated_regions.append(region)
            continue

        # コード領域と重複チェック
        overlapping = False
        for code in code_regions:
            if calculate_iou(region["bbox"], code["bbox"]) > 0:
                overlapping = True
                break

        if not overlapping:
            updated_regions.append(region)

    # コード領域を追加
    for code in code_regions:
        updated_regions.append({
            "type": "CODE",
            "label": "code",
            "bbox": code["bbox"],
            "confidence": code["confidence"]
        })

    return {**layout, "regions": updated_regions}
```

---

## 4. 依存パッケージ

### 新規追加

```text
opencv-python>=4.8.0
guesslang>=2.2.1
tensorflow>=2.10.0  # guesslang依存
```

### TensorFlow 影響

| 項目 | 影響 |
|------|------|
| ファイルサイズ | +500MB（仮想環境） |
| 推論速度 | <100ms/判定（CPU） |
| メモリ | +200MB（モデルロード時） |

**Rationale**: SC-004（性能低下≤20%）は達成可能。TensorFlowは初回ロードのみ重い。

---

## 5. 未解決事項

なし（全項目解決済み）
