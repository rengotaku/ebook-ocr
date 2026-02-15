# Phase 5 Output: User Story 4 - list/figure要素の出力（GREEN フェーズ）

**Date**: 2026-02-16
**Branch**: 009-converter-redesign

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 5 (GREEN) |
| タスク完了 | 10/10 (100%) |
| ステータス | 完了 |
| 実装ファイル | 3 |
| 新規関数 | 2 |

## 完了タスク

- [x] T064: REDテスト確認
- [x] T065: List に list_type 属性追加
- [x] T066: Figure を path, marker 属性に変更
- [x] T067: parse_list で list_type 判定
- [x] T068: 図プレースホルダー検出パターン追加
- [x] T069: transform_list で type 属性出力
- [x] T070: transform_figure を新形式に改修
- [x] T071: Phase 5 REDテスト PASS 確認
- [x] T072: リグレッション確認
- [x] T073: フェーズ出力生成

## 変更ファイル

### プロダクションコード

| ファイル | 変更内容 | 行数変更 |
|----------|---------|----------|
| src/book_converter/models.py | List.list_type 属性追加、Figure 新形式対応 | +5/-3 |
| src/book_converter/parser.py | parse_list 拡張、parse_figure_placeholder 追加 | +55/-10 |
| src/book_converter/transformer.py | transform_list 追加、transform_figure 新形式対応 | +65/-30 |

### 実装した機能

#### 1. List.list_type 属性 (T065)

リスト種別を識別するための属性を追加。

```python
@dataclass(frozen=True)
class List:
    """リスト"""
    items: tuple[str, ...]
    list_type: str = "unordered"  # "unordered" or "ordered"
    read_aloud: bool = True
```

**特徴**:
- デフォルト値: "unordered"
- 値: "unordered" (箇条書き) または "ordered" (番号付き)
- immutable (frozen dataclass)

#### 2. Figure 新形式対応 (T066)

path, marker 属性を追加し、シンプルな自己終了タグ形式に対応。

```python
@dataclass(frozen=True)
class Figure:
    """図表"""
    path: str  # 必須: 画像ファイルパス
    marker: str = ""  # オプション: 元のマーカーテキスト
    read_aloud: bool = False  # 常に False
    # 後方互換性のための属性（オプション）
    file: str = ""
    caption: str = ""
    description: str = ""
    continued: bool = False
```

**特徴**:
- **新形式**: path, marker, read_aloud (bool)
- **旧形式**: file, caption, description, continued (後方互換性維持)
- read_aloud デフォルト値を False に変更（図は読み上げない）

#### 3. parse_list 拡張 (T067)

リスト種別（unordered/ordered）を自動判定。

```python
def parse_list(lines: list[str]) -> List | None:
    """Parse list lines into a List object.

    処理:
    1. 最初の行でリストタイプを判定
       - "-" または "*" で始まる → unordered
       - 数字 + "." で始まる → ordered
    2. 各行をパターンマッチで解析
    3. リスト項目を抽出
    """
```

**判定ロジック**:
- Unordered pattern: `^\s*[-*]\s+(.*)$`
- Ordered pattern: `^\s*\d+\.\s+(.*)$`
- 最初の行でタイプを判定し、以降は同じパターンを適用

#### 4. parse_figure_placeholder 追加 (T068)

図プレースホルダーを検出する新規関数。

```python
def parse_figure_placeholder(line: str) -> dict | None:
    """図プレースホルダーを検出.

    対応パターン:
    - [図], [図1], [図 1], [図1-1]
    - [写真], [写真1]
    - [表], [表1]
    - [イラスト], [グラフ], [チャート]

    Returns:
        {"marker": "図1"} or None
    """
```

**特徴**:
- 正規表現: `\[(図|写真|表|イラスト|グラフ|チャート)([^\]]*)\]`
- 行内の任意の位置で検出（文中でも可）
- 複数ある場合は最初のもののみ返却

#### 5. transform_list 追加 (T069)

List を XML Element に変換する新規関数。

```python
def transform_list(lst: List) -> Element:
    """List を XML Element に変換.

    出力例:
    <list type="unordered">
      <item>項目1</item>
      <item>項目2</item>
    </list>
    """
```

**XML形式**:
- `<list type="unordered">` または `<list type="ordered">`
- 各項目は `<item>` 子要素として出力
- readAloud 属性は出力しない（デフォルトの true を想定）

#### 6. transform_figure 新形式対応 (T070)

新形式（自己終了タグ）と旧形式（子要素）を両対応。

```python
def transform_figure(figure: Figure) -> Element:
    """Transform a Figure object into an XML Element (新形式).

    新形式:
    <figure readAloud="false" path="figures/fig001.png" marker="図1" />

    旧形式（後方互換性）:
    <figure readAloud="optional" continued="true">
      <file readAloud="false">image.png</file>
      <caption readAloud="true">Caption</caption>
      <description>Description</description>
    </figure>
    """
```

**判定ロジック**:
- `figure.path` が存在 → 新形式（自己終了タグ）
- `figure.path` が空 → 旧形式（子要素）

**後方互換性**:
- file, caption, description 属性がある場合も正しく処理
- read_aloud が str 型（旧形式: "true"/"false"/"optional"）でも対応

## テスト結果

### Phase 5 REDテスト: 56/56 PASS

すべてのREDテストがPASSしてGREEN状態になりました:

- TestListTypeAttribute: 8/8 PASS
- TestTransformListType: 10/10 PASS
- TestFigurePathMarker: 10/10 PASS
- TestParseFigurePlaceholder: 18/18 PASS
- TestTransformFigureNewFormat: 10/10 PASS

**合計**: 56 PASS

### リグレッション

Phase 2, 3, 4 のテストもすべて通過:
- Phase 2 (US1): TocEntry.level int化 - すべてPASS
- Phase 3 (US2): StructureContainer, ページコメント - すべてPASS
- Phase 4 (US3): paragraph の論理的分離 - すべてPASS

既知の問題（Phase 2の破壊的変更による）:
- 既存テスト59件が失敗（TocEntry.level が str から int に変更されたため）
- これは Phase 2 で記録された既知の問題

## 実装の詳細

### T065: List.list_type 属性追加

既存の List dataclass に list_type フィールドを追加。

**変更前**:
```python
@dataclass(frozen=True)
class List:
    items: tuple[str, ...]
    read_aloud: bool = True
```

**変更後**:
```python
@dataclass(frozen=True)
class List:
    items: tuple[str, ...]
    list_type: str = "unordered"  # "unordered" or "ordered"
    read_aloud: bool = True
```

**影響範囲**:
- parse_list 関数の戻り値に list_type を追加
- transform_list 関数で list_type を type 属性に出力

### T066: Figure 新形式対応

path, marker 属性を追加し、後方互換性のため既存属性も維持。

**変更前**:
```python
@dataclass(frozen=True)
class Figure:
    file: str
    caption: str = ""
    description: str = ""
    read_aloud: str = "optional"  # "true", "false", "optional"
    continued: bool = False
```

**変更後**:
```python
@dataclass(frozen=True)
class Figure:
    path: str  # 必須: 画像ファイルパス
    marker: str = ""  # オプション: 元のマーカーテキスト
    read_aloud: bool = False  # 常に False
    # 後方互換性のための属性（オプション）
    file: str = ""
    caption: str = ""
    description: str = ""
    continued: bool = False
```

**設計判断**:
- path を第一引数（必須）に配置
- 既存属性はオプションとして維持（デフォルト値 = ""）
- read_aloud を bool 型に変更（旧形式は str 型）

### T067: parse_list 拡張

リストタイプ判定ロジックを追加。

**変更前**:
```python
# Unordered list のみ対応
pattern = r"^\s*[-*]\s+(.*)$"
```

**変更後**:
```python
# 最初の行で ordered/unordered を判定
unordered_pattern = r"^\s*[-*]\s+(.*)$"
ordered_pattern = r"^\s*\d+\.\s+(.*)$"

for line in lines:
    if not items:
        if re.match(ordered_pattern, line):
            list_type = "ordered"

    # リストタイプに応じてパターンマッチ
    if list_type == "ordered":
        match = re.match(ordered_pattern, line)
    else:
        match = re.match(unordered_pattern, line)
```

**エッジケース**:
- 空リスト → None 返却
- 最初の行で判定できない → デフォルト "unordered"

### T068: parse_figure_placeholder 追加

新規関数として parser.py に追加。

```python
def parse_figure_placeholder(line: str) -> dict | None:
    """図プレースホルダーを検出"""
    import re

    # Pattern: [図|写真|表|イラスト|グラフ|チャート][番号・記号] ]
    pattern = r"\[(図|写真|表|イラスト|グラフ|チャート)([^\]]*)\]"
    match = re.search(pattern, line)

    if match:
        marker = f"{match.group(1)}{match.group(2)}"
        return {"marker": marker}

    return None
```

**戻り値**:
- dict 形式: `{"marker": "図1"}`
- None: プレースホルダーが見つからない場合

### T069: transform_list 追加

新規関数として transformer.py に追加。

```python
def transform_list(lst: List) -> Element:
    """List を XML Element に変換"""
    elem = Element("list")
    elem.set("type", lst.list_type)

    for item_text in lst.items:
        item_elem = Element("item")
        item_elem.text = item_text
        elem.append(item_elem)

    return elem
```

**XML出力例**:
```xml
<list type="unordered">
  <item>項目1</item>
  <item>項目2</item>
</list>
```

### T070: transform_figure 新形式対応

既存関数を拡張して新形式に対応。

**判定ロジック**:
```python
# 新形式: path属性（自己終了タグ）
if figure.path:
    elem.set("path", figure.path)
    if figure.marker:
        elem.set("marker", figure.marker)
    # 新形式は自己終了タグのため、子要素なし
    return elem

# 旧形式: file/caption/description 子要素
# （後方互換性のため維持）
```

**XML出力例（新形式）**:
```xml
<figure readAloud="false" path="figures/fig001.png" marker="図1" />
```

**XML出力例（旧形式）**:
```xml
<figure readAloud="optional" continued="true">
  <file readAloud="false">image.png</file>
  <caption readAloud="true">Caption</caption>
  <description>Description</description>
</figure>
```

## 実装上の注意点

### immutability維持

- すべてのdataclassは frozen=True
- 新しいオブジェクトを生成（既存オブジェクトを変更しない）

### 後方互換性

- Figure の旧形式（file, caption, description）も引き続きサポート
- transform_figure が自動判定（path がある → 新形式、ない → 旧形式）

### エッジケース処理

- 空リスト → None 返却
- 図プレースホルダーなし → None 返却
- マーカーなし図 → marker 属性を出力しない

## 次フェーズへの引継ぎ事項

### Phase 6へのインプット

Phase 6 (CLI拡張 & Polish) では以下を実施:

1. **CLI引数追加**
   - `--figure-markers`: カスタム図マーカー指定

2. **廃止コード削除**
   - transform_page 関数（構造コンテナ移行により不要）
   - Page 関連の未使用コード

3. **テストクリーンアップ**
   - 既存テストの廃止コード参照を削除
   - Phase 2 の破壊的変更によるテスト更新

4. **カバレッジ確認**
   - `make coverage` で ≥80% 確認

### 残存課題

1. **parserロジック未統合**
   - `parse_figure_placeholder` は独立した関数として実装
   - 既存の `_parse_single_page_content` への統合は Phase 6 以降で検討

2. **既存 parse_figure との共存**
   - 既存の `parse_figure` 関数（<!-- FIGURE: path --> コメント解析）と新規 `parse_figure_placeholder` 関数（[図] プレースホルダー検出）が共存
   - 後方互換性のため既存関数は削除していない

3. **既存テストの更新**
   - Phase 2の破壊的変更（TocEntry.level型変更）に対応するテスト更新が未完了
   - 59件のテスト失敗が残存（既知の問題）

## 検証

```bash
# Phase 5 REDテスト全PASS確認
python -m pytest tests/book_converter/test_models.py::TestListTypeAttribute -v
python -m pytest tests/book_converter/test_models.py::TestFigurePathMarker -v
python -m pytest tests/book_converter/test_parser.py::TestParseFigurePlaceholder -v
python -m pytest tests/book_converter/test_transformer.py::TestTransformListType -v
python -m pytest tests/book_converter/test_transformer.py::TestTransformFigureNewFormat -v

# Phase 2, 3, 4 テスト確認（リグレッションなし）
python -m pytest tests/book_converter/test_models.py::TestTocEntryLevelInt -v
python -m pytest tests/book_converter/test_models.py::TestStructureContainer -v
python -m pytest tests/book_converter/test_transformer.py::TestTransformStructureContainer -v
python -m pytest tests/book_converter/test_xml_builder.py::TestPageCommentGeneration -v
python -m pytest tests/book_converter/test_parser.py::TestParseParagraphRemoveNewlines -v
python -m pytest tests/book_converter/test_parser.py::TestParagraphSplitByBlankLines -v
python -m pytest tests/book_converter/test_parser.py::TestWhitespaceOnlyLineAsBlank -v
python -m pytest tests/book_converter/test_parser.py::TestParagraphContinuationAcrossPages -v
```

## ステータス

**Phase 5 完了** - User Story 4 (list/figure要素の出力) の実装が完了。すべてのREDテストがPASSし、リグレッションなし。
