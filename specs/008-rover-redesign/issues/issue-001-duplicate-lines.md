# Issue 001: ROVER出力の行重複問題

**日付**: 2026-02-15
**発見場所**: `output/157012a97dcbebed/ocr_output/rover/page_0005.txt`
**重大度**: HIGH (出力品質に直接影響)
**ステータス**: ✅ RESOLVED (commit: c2b71a5)

## 症状

rover出力で同一内容の行が重複して出力される。

```
2→このたびは翔泳社の書籍をお買い上げいただき誠にありがとうございます。 幣社では、読者の
3→このたびは翔泳社の書籍をお買い上げいただき、誠にありがとうございます。弊社では、読者の
```

## 根本原因

### 1. yomitokuの段落検出による行マージ

**実測データ:**

| エンジン | Line | y_center | y_range | 内容 |
|---------|------|----------|---------|------|
| **yomitoku** | 2 | **223.0** | **[169-277]** | 「このたびは...弊社では、読者の皆様からの...」|
| paddleocr | 2 | 182.5 | [168-197] | 「このたびは...読者の」|
| paddleocr | 3 | 221.5 | [207-236] | 「皆様からの...」|
| paddleocr | 4 | 261.0 | [247-275] | 「願い致しております...」|
| easyocr | 2 | 185.0 | - | 「このたびは...」|
| easyocr | 3 | 225.0 | - | 「皆様からの...」|

**問題点:**
- yomitokuは**段落単位**で認識 → 複数の物理行を1行として返す
- y_range = [169-277] は paddleocr の3行分に相当 (Line 2,3,4)
- yomitoku の y_center = 223.0 は段落中央の値

### 2. align_lines_by_y のマッチングエラー

```
y_tolerance = 30 でのアライメント:

y≈183 (paddleocr Line2 + easyocr Line2):
  - yomitoku Line2 (y=223) は範囲外 (223-183=40 > 30)
  → AlignedLine 2: {paddleocr, easyocr} のみ
  → 投票結果: 「このたびは...幣社では...」(easyocrの誤字含む)

y≈223 (paddleocr Line3 + easyocr Line3 + yomitoku Line2):
  - yomitoku Line2 (y=223) がマッチ!
  → AlignedLine 3: {paddleocr, easyocr, yomitoku}
  → 投票結果: 「このたびは...弊社では...」(yomitokuの内容が勝つ)

結果: 同じ内容が2回出力される
```

### 3. 図解

```
物理的な行位置:
y=169-197: 「このたびは翔泳社の書籍を...読者の」
y=207-236: 「皆様からのお問い合わせに...協力をお」
y=247-275: 「願い致しております...」

yomitokuの認識:
[============ 1つの段落 (y=169-277) ============]
  y_center = 223 (中央値)

paddleocr/easyocrの認識:
[--- Line2 ---] [--- Line3 ---] [--- Line4 ---]
  y=183          y=222          y=261

アライメント (y_tolerance=30):
  y=183 → paddleocr+easyocr (yomitoku y=223 は範囲外)
  y=222 → paddleocr+easyocr+yomitoku (yomitoku y=223 がマッチ)
  y=261 → paddleocr+easyocr (yomitoku既使用)
```

## 解決案

### 案A: yomitoku段落の物理行分割 (推奨)

yomitokuの段落内でy座標のギャップを検出し、物理行に分割する。

```python
def split_paragraph_to_physical_lines(
    items: list[TextWithBox],
    y_gap_threshold: int = 15,
) -> list[list[TextWithBox]]:
    """段落内のアイテムをy座標ギャップで物理行に分割"""
    if not items:
        return []

    # y座標でソート
    sorted_items = sorted(items, key=lambda x: x.y_center)

    lines = []
    current_line = [sorted_items[0]]

    for item in sorted_items[1:]:
        # 前のアイテムとのy座標差をチェック
        prev_y = current_line[-1].y_center
        if item.y_center - prev_y > y_gap_threshold:
            # 新しい行開始
            lines.append(current_line)
            current_line = [item]
        else:
            current_line.append(item)

    if current_line:
        lines.append(current_line)

    return lines
```

**適用場所:** `cluster_lines_by_y` の前処理、またはyomitoku専用

**シミュレーション結果:**

```
適用前:
  yomitoku Line 2: y_center=223.0, y_range=[169-277]
  → 3行分の内容が1行に

適用後:
  yomitoku Line 2a: y_center=185.0, y_range=[169-197] ← paddleocr Line2とマッチ
  yomitoku Line 2b: y_center=222.0, y_range=[207-236] ← paddleocr Line3とマッチ
  yomitoku Line 2c: y_center=261.0, y_range=[247-275] ← paddleocr Line4とマッチ

アライメント結果:
  y≈183: paddleocr Line2 + easyocr Line2 + yomitoku Line2a ✓
  y≈222: paddleocr Line3 + easyocr Line3 + yomitoku Line2b ✓
  y≈261: paddleocr Line4 + easyocr Line4 + yomitoku Line2c ✓

→ 重複なし!
```

### 案B: yomitoku wordsの直接使用

yomitokuの `paragraphs` ではなく `words` を使用して行検出。
wordsは個々の単語単位なので、物理行に近いy座標を持つ。

### 案C: 多数決による重複除去 (対症療法)

最終出力で類似度が高い隣接行を除去。根本解決ではない。

## 推奨対応

1. **案A実装**: yomitoku段落の物理行分割
2. **テスト追加**: 段落が複数行にまたがるケースのテスト
3. **検証**: 他のページでも重複が解消されることを確認

## 影響を受ける関数

- `src/ocr_rover.py:cluster_lines_by_y` - 分割処理を追加
- `src/ocr_engines.py:run_yomitoku_with_boxes` - words使用に変更の可能性

## テストケース追加

```python
def test_yomitoku_paragraph_split_to_physical_lines():
    """yomitokuの段落が複数の物理行に分割される"""
    # Setup: y_range=[169-277]の段落、y_gap=10で3行に分割
    # Assert: 3つのOCRLineが生成される

def test_rover_no_duplicate_with_multiline_paragraph():
    """yomitoku段落が複数行でも重複しない"""
    # Setup: yomitoku 1段落 vs paddleocr 3行
    # Assert: 出力は3行のみ、重複なし
```

## 解決 (2026-02-15)

**採用案**: 案B (yomitoku wordsの直接使用) のバリエーション

### 実装内容

1. `run_yomitoku_with_boxes` を `words` ベースに変更
2. `_cluster_words_to_lines` 関数を追加 - words を y座標でクラスタリング
3. 各物理行が個別の `TextWithBox` として返される

### 修正ファイル

- `src/ocr_engines.py`: `run_yomitoku_with_boxes`, `_cluster_words_to_lines`
- `src/ocr_rover.py`: `split_multiline_items` (補助関数として残存)
- `tests/test_ocr_rover.py`: 10件のテスト追加

### 検証結果

```
修正前:
  yomitoku Line 2: y_center=223.0, y_range=[169-277] (3行分)
  yomitoku 行数: 20行
  rover 出力: 32行 (重複あり)

修正後:
  yomitoku Line 2: y_center=181.5, y_range=[166-197] (1行)
  yomitoku 行数: 26行 (paddleocr/easyocrと同等)
  rover 出力: 26行 (重複なし)
```

### テスト結果

```
147 passed in 0.17s
```
