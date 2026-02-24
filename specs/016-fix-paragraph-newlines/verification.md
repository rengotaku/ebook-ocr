# Issue#21 修正検証: paragraphタグの改行問題

**検証日**: 2026-02-24
**対象ファイル**: `src/book_converter/parser/paragraph.py`
**対象関数**: `parse_paragraph`

## 入力データ（Issue#21のサンプル）

```
Line 1: '出石聡史うまい進めかたチーム開発の'
Line 2: '42の失敗事例で学ぶ'
Line 3: 'DEISHI SATOSHI'
Line 4: 'ソフトウェア'
Line 5: '開発現場の'
Line 6: 'と'
Line 7: '「失敗」集め'
Line 8: 'よくある落とし穴の回避策がわかる!'
```

## 修正前の出力

**コード**: `text = "\n".join(lines).strip()`

```xml
<paragraph readAloud="true">出石聡史うまい進めかたチーム開発の
42の失敗事例で学ぶ
DEISHI SATOSHI
ソフトウェア
開発現場の
と
「失敗」集め
よくある落とし穴の回避策がわかる!</paragraph>
```

- 文字数: 83文字
- 改行数: **7個** ❌

## 修正後の出力

**コード**:
```python
text = "".join(line.strip() for line in lines)  # ブランク結合
text = re.sub(r"\s+", " ", text).strip()
```

```xml
<paragraph readAloud="true">出石聡史うまい進めかたチーム開発の42の失敗事例で学ぶDEISHI SATOSHIソフトウェア開発現場のと「失敗」集めよくある落とし穴の回避策がわかる!</paragraph>
```

- 文字数: 76文字
- 改行数: **0個** ✅

## 検証結果

| 項目 | 修正前 | 修正後 | 状態 |
|------|--------|--------|------|
| 改行文字 | 7個含む | 0個 | ✅ |
| 余分な空白 | - | なし | ✅ |
| 単一行出力 | ❌ | ✅ | ✅ |
| テスト | - | 51件パス | ✅ |
| Lint | - | パス | ✅ |

## 結論

修正により、`<paragraph>`タグ内の不要な改行が除去され、ブランク結合による単一行フォーマットで出力されることを確認。後処理で詰める処理が不要になる。
