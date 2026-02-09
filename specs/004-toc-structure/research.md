# Research: 目次情報の保持

**Date**: 2026-02-08
**Feature**: 004-toc-structure

## 1. 既存モジュール構造

### 1.1 models.py パターン

**Decision**: 既存のfrozen dataclassパターンに従う

**Rationale**:
- Constitution IV（Immutability）に準拠
- 既存のPage, Content, Headingなどと一貫性を保つ
- tupleベースのコレクションで不変性を保証

**Pattern**:
```python
@dataclass(frozen=True)
class TocEntry:
    text: str
    level: str  # "chapter", "section", "subsection", "other"
    number: str = ""
    page: str = ""
    read_aloud: bool = False

@dataclass(frozen=True)
class TableOfContents:
    entries: tuple[TocEntry, ...]
    read_aloud: bool = False
```

### 1.2 parser.py パターン

**Decision**: 既存のFIGUREコメント解析パターンに従う

**Rationale**:
- `parse_figure_comment()`と同様のregexベースのマーカー検出
- 大文字小文字不区別（`[Tt][Oo][Cc]`）
- Noneを返すエラーハンドリング

**Pattern**:
```python
def parse_toc_marker(line: str) -> str | None:
    """Detect <!-- toc --> or <!-- /toc --> marker."""
    pattern = r"<!--\s*(/?)\s*toc\s*-->"
    match = re.search(pattern, line, re.IGNORECASE)
    if match:
        return "start" if not match.group(1) else "end"
    return None
```

### 1.3 transformer.py パターン

**Decision**: 既存のtransform_*関数パターンに従う

**Rationale**:
- Element/SubElementベースのXML生成
- 属性設定はset()メソッド
- readAloud属性の継承パターンを踏襲

**Pattern**:
```python
def transform_toc_entry(entry: TocEntry) -> Element:
    elem = Element("entry")
    elem.set("level", entry.level)
    if entry.number:
        elem.set("number", entry.number)
    elem.set("title", entry.text)
    if entry.page:
        elem.set("page", entry.page)
    return elem
```

## 2. 目次エントリ解析

### 2.1 章番号パターン

**Decision**: 日本語書籍の標準的なパターンをサポート

**Patterns**:

| パターン | 正規表現 | level | number抽出 |
|---------|---------|-------|-----------|
| 第N章 | `^第(\d+)章\s+(.+)` | chapter | \1 |
| N.N | `^(\d+\.\d+)\s+(.+)` | section | \1 |
| N.N.N | `^(\d+\.\d+\.\d+)\s+(.+)` | subsection | \1 |
| その他 | 上記以外 | other | "" |

**Rationale**:
- 日本語技術書で最も一般的な形式
- 番号なしエントリ（「はじめに」「おわりに」）はlevel="other"

### 2.2 ページ番号抽出

**Decision**: 行末のページ番号パターンを検出

**Patterns**:
```python
# ドットリーダー形式: "章タイトル ... 15"
pattern1 = r"\.{2,}\s*(\d+)\s*$"

# 罫線形式: "章タイトル ─── 15"
pattern2 = r"[─\-]{2,}\s*(\d+)\s*$"

# 空白区切り形式: "章タイトル    15"
pattern3 = r"\s{3,}(\d+)\s*$"
```

**Rationale**:
- OCR処理後の目次ではドットリーダーが多い
- 複数パターンを試行して最初にマッチしたものを使用

## 3. マーカー状態管理

### 3.1 マーカースタック

**Decision**: スタックベースのネスト管理

**Rationale**:
- `<!-- content -->` と `<!-- skip -->` のネストを正しく処理
- 内側のマーカーが優先される仕様を実現

**Pattern**:
```python
@dataclass
class MarkerState:
    stack: list[str] = field(default_factory=list)  # ["content", "skip", ...]

    @property
    def current_read_aloud(self) -> bool:
        if not self.stack:
            return False  # デフォルトはfalse
        return self.stack[-1] == "content"
```

### 3.2 ページ境界でのリセット

**Decision**: マーカー状態はページをまたいで継続

**Rationale**:
- 目次が複数ページにまたがるケースに対応
- `<!-- /toc -->`が出現するまで目次収集を継続

## 4. XSDスキーマ拡張

### 4.1 既存スキーマ確認

**Finding**: 既存のbook.xsdには`<toc>`と`<tocItem>`が定義済み

**Decision**: 仕様書の`<tableOfContents>`と`<entry>`形式に変更

**Rationale**:
- 仕様書で決定した構造（`<tableOfContents><entry .../>`）を優先
- 既存の`<toc>`は使用しない（命名の一貫性のため）

### 4.2 新規スキーマ定義

```xml
<xs:element name="tableOfContents">
  <xs:complexType>
    <xs:sequence>
      <xs:element ref="entry" maxOccurs="unbounded"/>
    </xs:sequence>
    <xs:attribute name="readAloud" type="xs:boolean" default="false"/>
  </xs:complexType>
</xs:element>

<xs:element name="entry">
  <xs:complexType>
    <xs:attribute name="level" use="required">
      <xs:simpleType>
        <xs:restriction base="xs:string">
          <xs:enumeration value="chapter"/>
          <xs:enumeration value="section"/>
          <xs:enumeration value="subsection"/>
          <xs:enumeration value="other"/>
        </xs:restriction>
      </xs:simpleType>
    </xs:attribute>
    <xs:attribute name="number" type="xs:string"/>
    <xs:attribute name="title" type="xs:string" use="required"/>
    <xs:attribute name="page" type="xs:string"/>
  </xs:complexType>
</xs:element>
```

## 5. 後方互換性

### 5.1 既存動作の維持

**Decision**: マーカーなしの場合は既存動作を維持

**Implementation**:
- マーカーがない場合、`tableOfContents`要素は生成しない
- 既存のreadAloud属性のデフォルト値を変更（false→true→false）

**Rationale**:
- 既存のbook.mdファイルが破壊されない
- 段階的な移行が可能

### 5.2 デフォルトreadAloud変更

**Breaking Change**: デフォルトがtrue→falseに変更

**Mitigation**:
- 既存ファイルには`<!-- content -->`マーカーを追加する必要がある
- ドキュメントで移行手順を明記

## 6. テスト戦略

### 6.1 単体テスト

| テスト対象 | テストケース |
|-----------|-------------|
| parse_toc_marker | 開始/終了マーカー、大文字小文字 |
| parse_content_marker | content/skip/終了マーカー |
| parse_toc_entry | 章/節/項パターン、ページ番号抽出 |
| transform_toc_entry | XML属性生成 |
| transform_table_of_contents | 複数エントリ変換 |

### 6.2 統合テスト

| シナリオ | 入力 | 期待出力 |
|---------|-----|---------|
| 目次のみ | `<!-- toc -->`...`<!-- /toc -->` | `<tableOfContents>` |
| 本文のみ | `<!-- content -->`...`<!-- /content -->` | 各要素に`readAloud="true"` |
| 混合 | 目次+本文+索引 | 正しいreadAloud属性 |
| マーカーなし | 既存book.md | 全要素`readAloud="false"` |

## 7. 代替案の検討

### 7.1 自動TOC検出

**Rejected**: パターンベースの自動検出

**Reason**:
- 誤検出リスクが高い
- 手動マーカーの方が確実で運用コストが低い

### 7.2 YAML設定ファイル

**Rejected**: 外部設定ファイルでの範囲指定

**Reason**:
- book.mdと設定ファイルの同期が必要
- インラインマーカーの方がシンプル
