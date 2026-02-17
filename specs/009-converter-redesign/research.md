# Research: Converter再設計

**Date**: 2026-02-16
**Branch**: 009-converter-redesign

## 1. 既存コードベース分析

### 現在の構造

```
src/book_converter/
├── models.py         # データモデル（frozen dataclass）
├── parser.py         # MDパーサー（1305行）
├── transformer.py    # XML変換（390行）
├── xml_builder.py    # XML生成（142行）
├── cli.py            # CLIエントリポイント
├── config.py         # 設定管理
├── analyzer.py       # 分析ユーティリティ
├── toc_classifier.py # TOC分類（LLM対応）
├── page_grouper.py   # ページグループ化
└── errors.py         # エラー定義
```

### 現在のデータモデル (models.py)

| Entity | 現状 | 変更必要性 |
|--------|------|-----------|
| `TocEntry` | level="chapter"/"section"/"subsection"/"other" | → level=1-5 (数値) |
| `Page` | 構造コンテナとして使用 | → `<page>` 廃止、XMLコメント化 |
| `Heading` | level=1-3 | → level=1-5 |
| `Paragraph` | 改行を保持 | → 改行除去、連続テキスト化 |
| `Figure` | file, caption, description | → path属性追加、readAloud=false |
| `List` | items tuple | そのまま使用可 |
| `HeaderLevelConfig` | level1-5対応済み | そのまま使用可 |

### 現在のパーサー (parser.py)

**問題点:**
1. `parse_paragraph()`: 改行を`\n`で結合（改行除去が必要）
2. `parse_toc_entry()`: level文字列（"chapter"/"section"等）を返す（数値化が必要）
3. TOC階層: `level="other"` にフォールバック（全レベル対応が必要）

### 現在のXML出力 (transformer.py)

**問題点:**
1. `transform_page()`: `<page>` 要素を生成（廃止が必要）
2. `transform_content()`: `<content>` ラッパーを生成（不要な可能性）
3. 構造コンテナ（chapter/section）が存在しない（追加が必要）

## 2. 設計決定

### Decision 1: TOC階層レベルの数値化

**Decision**: TocEntry.level を int (1-5) に変更

**Rationale**:
- 文字列（"chapter"等）は書籍固有で汎用性がない
- CLI引数 `--header-level1` 〜 `--header-level5` と直接対応
- MDの見出しレベル（#=1, ##=2, ...）と一致

**Alternatives considered**:
- 文字列のまま維持 → 拒否：キーワード依存で柔軟性欠如

### Decision 2: 構造コンテナの導入

**Decision**: 新しい構造コンテナモデル（StructureContainer）を導入

**Rationale**:
- `<chapter>`, `<section>` などの構造コンテナが必要
- ページ要素（`<page>`）は廃止
- heading要素は読み上げ専用として分離

**Implementation**:
```python
@dataclass(frozen=True)
class StructureContainer:
    container_type: str  # "chapter", "section", "subsection", etc.
    level: int           # 1-5
    number: str          # "1", "2", etc.
    title: str           # コンテナのタイトル（ナビゲーション用）
    children: tuple      # 子要素（StructureContainer or ContentElement）
```

**Alternatives considered**:
- Pageをコンテナとして維持 → 拒否：ページ概念は論理構造に不要

### Decision 3: Paragraph改行処理

**Decision**: paragraph内のソフト改行を除去し、連続テキスト化

**Rationale**:
- 読み上げ時に不自然な間が入らない
- 空行のみが段落区切り（FR-005）

**Implementation**:
- `parse_paragraph()`: `\n` を空白に置換、連続空白を単一空白に圧縮
- 空行検出: スペース/タブのみの行も空行として扱う

**Alternatives considered**:
- 改行を維持 → 拒否：読み上げ品質低下

### Decision 4: ページ情報のXMLコメント化

**Decision**: `<page>` 要素を廃止し、`<!-- page N -->` コメントに変更

**Rationale**:
- ページは物理的概念で論理構造に不要（FR-008）
- 読み上げ対象外
- デバッグ/参照用に位置情報は保持

**Implementation**:
- xml_builder: `Comment(f" page {page_number} ")` を挿入
- transformer: transform_page() を廃止

**Alternatives considered**:
- ページ要素を維持 → 拒否：論理構造と物理構造の混同

### Decision 5: Figure要素の形式

**Decision**: `<figure readAloud="false" path="xxx.png">` 形式

**Rationale**:
- プレースホルダー検出後、実画像パスを属性に設定
- 読み上げ対象外（readAloud="false"）

**Implementation**:
- MDで `[図]`, `[写真]`, `[表]` 等を検出
- figuresフォルダから対応画像を参照
- path属性に相対パスを設定

**Alternatives considered**:
- caption/description子要素を維持 → 保留：必要に応じて追加可能

## 3. 変更影響分析

### 変更が必要なファイル

| ファイル | 変更内容 | 影響度 |
|----------|----------|--------|
| models.py | TocEntry.level数値化、StructureContainer追加、Figure拡張 | 高 |
| parser.py | paragraph改行除去、TOC level数値化、figure検出追加 | 高 |
| transformer.py | transform_page廃止、structure container変換追加 | 高 |
| xml_builder.py | 構造コンテナベースの生成ロジック | 高 |
| cli.py | --figure-markers引数追加 | 低 |

### 後方互換性

- **破壊的変更**: XML出力形式が根本的に変わる
- **移行戦略**: 新バージョンとして導入（v2）

## 4. テスト戦略

### 単体テスト

1. **models**: StructureContainer, TocEntry(level=int)
2. **parser**: paragraph改行除去、空行検出、figure検出
3. **transformer**: 構造コンテナ変換、ページコメント生成
4. **xml_builder**: 完全なXML生成

### 統合テスト

1. MD→XML変換の完全フロー
2. 既存書籍データでの回帰テスト（5冊以上）

## 5. 実装順序

1. **Phase 1: データモデル拡張**
   - TocEntry.level を int に変更
   - StructureContainer 追加
   - Figure に path 属性追加

2. **Phase 2: パーサー改修**
   - paragraph 改行除去
   - 空行検出（スペースのみも含む）
   - figure プレースホルダー検出
   - TOC level 数値化

3. **Phase 3: トランスフォーマー改修**
   - transform_page() 廃止
   - 構造コンテナ変換追加
   - ページコメント生成

4. **Phase 4: XMLビルダー改修**
   - 構造コンテナベースの生成
   - ページコメント挿入

5. **Phase 5: CLI拡張**
   - --figure-markers 引数追加
