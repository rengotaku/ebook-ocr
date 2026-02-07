# Research: heading要素へのreadAloud属性付与ルール

**Date**: 2026-02-08
**Feature**: 003-heading-readaloud-rules

## 調査項目

### 1. 柱（ランニングヘッド）検出アルゴリズム

**Decision**: 最頻出heading level="1"テキストを柱として検出

**Rationale**:
- 柱は各ページに繰り返し出現するため、出現頻度が最も高いheading level="1"を柱と判定
- 閾値: 総ページ数の50%以上に出現するheadingを柱候補とする
- 表記揺れ（ダッシュの種類等）は正規化して比較

**Alternatives considered**:
1. 固定パターンマッチング → 書籍ごとにパターンが異なるため不採用
2. 機械学習ベース → 過剰な複雑性、YAGNI違反
3. ユーザー指定のみ → 自動化メリットがない

### 2. パターンマッチング戦略

**Decision**: 正規表現ベースのパターンマッチング + 設定ファイル外部化

**Rationale**:
- Pythonの`re`モジュールは高速で信頼性が高い
- パターンを外部ファイル化することで、書籍ごとのカスタマイズが可能
- 優先度付きパターンリストで、最初にマッチしたルールを適用

**Default patterns**:
```python
DEFAULT_EXCLUSION_PATTERNS = [
    # 高優先度: 柱（動的検出）
    {"id": "running-head", "priority": 100, "type": "dynamic"},
    # 高優先度: ページ番号表記
    {"id": "page-number", "priority": 90, "pattern": r".*[―—]\s*\d+\s*/\s*\d+$"},
    # 中優先度: 章節ラベル
    {"id": "section-label", "priority": 50, "pattern": r"^Section\s+\d+\.\d+$"},
    # 中優先度: 装飾記号
    {"id": "decoration", "priority": 50, "pattern": r"^[◆◇■□●○▲△]+$"},
    # 低優先度: 参照表記
    {"id": "reference", "priority": 30, "pattern": r"^Webサイト$"},
    # 低優先度: 脚注番号
    {"id": "footnote", "priority": 30, "pattern": r"^注\d+\.\d+"},
]
```

**Alternatives considered**:
1. ハードコード → 拡張性がない
2. 完全動的検出 → 偽陽性リスクが高い

### 3. level再配置ロジック

**Decision**: 柱テキスト検出後、level 2,3の同一テキストをlevel 1に再配置

**Rationale**:
- OCRやマークアップの揺れでlevelがずれることがある
- 柱として検出されたテキストは、どのlevelで出現しても同じ扱いをすべき
- 再配置は変換時に行い、元データは保持

**Implementation approach**:
1. 全headingを収集してHeadingAnalysisを構築
2. 柱テキストを特定（最頻出level=1）
3. 柱テキストがlevel 2,3で出現している場合、新しいHeadingオブジェクトをlevel=1で作成
4. readAloud="false"を付与

### 4. 設定ファイル形式

**Decision**: Python辞書形式（config.py）+ オプションでYAML/JSON

**Rationale**:
- シンプルな実装が可能
- 型チェックが効く
- 外部依存なし（pyyamlは追加依存）
- ユーザーがカスタマイズする場合はconfig.local.pyを作成

**Alternatives considered**:
1. YAML → pyyaml依存が追加
2. JSON → コメントが書けない
3. TOML → Python 3.11+標準だがoverkill

### 5. 既存コードへの影響

**Decision**: 最小限の変更で統合

**Files to modify**:
- `models.py`: ExclusionPattern, HeadingAnalysis追加
- `transformer.py`: transform_heading関数にreadAloud属性付与ロジック追加

**Files to create**:
- `analyzer.py`: heading頻度分析、柱検出
- `config.py`: デフォルトパターン定義

**No changes required**:
- `parser.py`: 既存のパース処理は変更なし
- `xml_builder.py`: 既存のシリアライズ処理は変更なし

## 結論

すべての技術的な不明点が解決されました。Phase 1のデザインに進むことができます。
