# Phase 1 Output: Setup

**Date**: 2026-02-21
**Status**: Complete

## T001: 既存のレイアウト検出実装確認

**File**: `src/layout/detector.py`

### 概要
yomitokuベースのレイアウト検出モジュール。

### 主要関数
- `detect_layout_yomitoku()`: メイン検出関数（pages_dir → layout.json）
- `paragraphs_to_layout()`: yomitoku結果 → layout形式変換
- `visualize_layout()`: バウンディングボックス可視化
- `save_yomitoku_results()` / `load_yomitoku_results()`: キャッシュ機能

### 現在のRegion Types
| Type | Label | 用途 |
|------|-------|------|
| TEXT | "plain text" | 本文段落 |
| TITLE | "section_headings" | 見出し |
| FIGURE | "figure" | 図表 |

### 統合ポイント
- **CODE region追加**: `paragraphs_to_layout()`の後にcode_detector処理を挿入
- layout.jsonフォーマット:
  ```json
  {
    "regions": [
      {"type": "TEXT|TITLE|FIGURE", "label": "...", "bbox": [x1,y1,x2,y2], "confidence": 1.0}
    ],
    "page_size": [width, height]
  }
  ```

---

## T002: 既存のbook_converterモデル確認

**File**: `src/book_converter/models.py`

### 現在のSectionElement
```python
SectionElement = Union[Heading, Paragraph, List, Figure]
```

### 変更計画
```python
# After
SectionElement = Union[Heading, Paragraph, List, Figure, Code]
```

### 既存dataclassパターン（参考: Figure）
```python
@dataclass(frozen=True)
class Figure:
    path: str           # 必須
    caption: str = ""   # オプション
    marker: str = ""    # オプション
```

### Code dataclass設計（data-model.md準拠）
```python
@dataclass(frozen=True)
class Code:
    text: str                    # コード本体
    confidence: float = 1.0      # Guesslang判定確率
    read_aloud: bool = False     # 常にFalse（TTS除外）
```

---

## T003: 既存のXMLビルダー確認

**File**: `src/book_converter/xml_builder.py`

### 構造
- `build_xml()`: Book → XML文字列
- transformer.pyに変換処理を委譲

**File**: `src/book_converter/transformer.py`

### transform_section パターン
```python
def transform_section(section: Section) -> Element:
    for child in section.elements:
        if isinstance(child, Paragraph):
            child_elem = transform_paragraph(child)
        elif isinstance(child, Heading):
            child_elem = transform_heading(child)
        elif isinstance(child, List):
            child_elem = transform_list(child)
        elif isinstance(child, Figure):
            child_elem = transform_figure(child)
        # ← Code追加予定
        elem.append(child_elem)
```

### readAloud属性パターン
```python
# Paragraph/Heading/List: read_aloud=Falseの場合のみ出力
if not para.read_aloud:
    elem.set("readAloud", "false")

# Figure: 常にreadAloud出力なし（読まない前提）
```

### Code要素出力設計
```python
def transform_code(code: Code) -> Element:
    elem = Element("code")
    elem.set("readAloud", "false")  # 常にfalse
    elem.text = code.text  # 改行・インデント保持
    return elem
```

---

## T004: 既存のパーサー構造確認

**Directory**: `src/book_converter/parser/`

### 既存ファイル
| File | 用途 |
|------|------|
| `__init__.py` | パッケージ初期化 |
| `heading.py` | 見出しパース |
| `paragraph.py` | 段落パース |
| `figure.py` | 図表パース |
| `toc.py` | 目次パース |
| `page.py` | ページパース |
| `models.py` | パーサー用モデル |
| `utils.py` | ユーティリティ |

### 追加予定
| File | 用途 |
|------|------|
| `code.py` | **NEW**: コード領域パース |

### パーサー統合ポイント
- layout.jsonのCODE領域 → Code dataclass生成
- `__init__.py`にcode parser export追加

---

## T005: 依存関係確認

**File**: `requirements.txt`

### 現在の依存
```
Pillow
imagehash
doclayout-yolo
requests
pyyaml
pytest
pytest-cov
pytesseract>=0.3.10
easyocr>=1.7.0
paddlepaddle>=2.5.0
paddleocr>=2.7.0
yomitoku>=0.10.0
pylint>=3.0.0
```

### 追加必要（research.md準拠）
```
opencv-python>=4.8.0   # OpenCV枠線検出
guesslang>=2.2.1       # コード判定
# tensorflow>=2.10.0   # guesslang依存（自動インストール）
```

### 注記
- `cv2`は`detector.py`で既に使用されているが、`opencv-python`がrequirements.txtに明示されていない
- guesslang追加時にTensorFlowが依存として入る（+500MB）

---

## 統合設計サマリー

### 処理フロー
```
[画像] → [yomitoku] → [layout.json v1]
                            ↓
                    [code_detector] ← NEW
                            ↓
                    [layout.json v2] (CODE領域追加)
                            ↓
                      [book.md via OCR]
                            ↓
                      [parser] ← code.py追加
                            ↓
                    [Code dataclass]
                            ↓
                    [transformer] ← transform_code追加
                            ↓
                    [<code readAloud="false">]
```

### 新規ファイル
1. `src/layout/code_detector.py` - コード検出ロジック
2. `src/book_converter/parser/code.py` - コードパーサー

### 変更ファイル
1. `src/book_converter/models.py` - Code dataclass + SectionElement更新
2. `src/book_converter/transformer.py` - transform_code追加
3. `requirements.txt` - opencv-python, guesslang追加

---

## 次フェーズへの準備

- ✅ 既存コード構造理解完了
- ✅ 統合ポイント特定完了
- ✅ 依存関係確認完了
- → Phase 2: コード検出コア機能（TDD）へ進行可能
