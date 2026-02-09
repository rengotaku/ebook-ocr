# Research: TOC構造を利用したpageタグのグルーピング

**Date**: 2026-02-09
**Feature**: 005-toc-page-grouping

## 調査項目

本機能は標準ライブラリのみを使用するシンプルなXML変換であり、重大なNEEDS CLARIFICATIONはありませんでした。以下は設計判断の記録です。

---

### 1. XMLパーサーの選択

**Decision**: `xml.etree.ElementTree` を使用

**Rationale**:
- Python標準ライブラリに含まれており、追加依存なし
- 本プロジェクトの既存コード（xml_builder.py）で既に使用されている
- シンプルなDOM操作に十分な機能を提供
- 処理対象のbook.xmlは数百KB〜数MB程度であり、メモリ効率は問題にならない

**Alternatives considered**:
- `lxml`: より高機能だが外部依存が増える。Constitution V (YAGNI) に反する
- `minidom`: 標準ライブラリだがAPIがやや複雑。既存コードとの一貫性を欠く

---

### 2. セクション番号抽出パターン

**Decision**: 2段階の正規表現パターンを使用

**Pattern 1 - pageMetadata用**:
```python
r'^(\d+(?:\.\d+)*)[\s　]'  # 例: "2.1 SLOを理解する — 2 / 7"
```

**Pattern 2 - heading用**:
```python
r'Section\s+(\d+(?:\.\d+)*)'  # 例: "Section 1.1"
r'^(\d+(?:\.\d+)*)\s'         # 例: "1.1.3 信頼性を制御する"
```

**Rationale**:
- 実データ分析に基づくパターン設計
- 全角スペース（`　`）にも対応
- セクション番号の階層（1, 1.1, 1.1.1）を柔軟に抽出

**Alternatives considered**:
- 単一パターン: カバレッジが不十分
- 機械学習ベース: 過剰な複雑性。Constitution V に反する

---

### 3. ページ所属判定アルゴリズム

**Decision**: 優先順位付き抽出 + フォールバック

**Algorithm**:
1. pageMetadataからセクション番号を抽出（最優先）
2. 失敗した場合、headingからセクション番号を抽出
3. 失敗した場合、直前のページと同じセクションに配置

**Rationale**:
- pageMetadataは構造化されており信頼性が高い
- headingは補完的な情報源
- フォールバックにより100%のページ配置を保証

**Alternatives considered**:
- ページ番号ベースの推測: 精度が低い
- すべての情報源を組み合わせた投票: 過剰に複雑

---

### 4. 章扉ページ判定ロジック

**Decision**: コンテンツパターンマッチング

**Criteria**:
- 「第N章」または章番号を含む
- 章タイトルを含む
- paragraph/heading以外のコンテンツが少ない（図表なし or 1つのみ）

**Rationale**:
- 実データの章扉ページの特徴に基づく
- シンプルなヒューリスティックで90%以上の精度が期待できる

---

### 5. 既存パイプラインへの統合

**Decision**: 独立モジュール + CLIオプション

**Integration Point**:
```python
# cli.py への追加
parser.add_argument('--group-pages', action='store_true')

# 処理フロー
book_xml = parse_and_build(book_md)
if args.group_pages:
    book_xml = group_pages_by_toc(book_xml)
save(book_xml)
```

**Rationale**:
- オプショナルな機能として既存フローに影響を与えない
- 既存のXML出力後に適用可能
- Constitution I (Pipeline-First) に準拠

---

## 結論

すべての技術的選択が決定済み。Phase 1 (Design & Contracts) に進む準備完了。
