# Phase 2 Output: User Story 1 - 繰り返し柱の自動除外 (GREEN)

**日付**: 2026-02-08
**フェーズ**: Phase 2 - User Story 1（繰り返し柱の自動除外）
**ステータス**: ✅ Complete (GREEN)

## 実施内容サマリー

User Story 1の実装を完了しました。柱（ランニングヘッド）とページ番号表記を自動検出し、`readAloud="false"`属性を付与する機能をTDDフローで実装しました。

## 完了タスク

| ID | タスク | 結果 |
|----|--------|------|
| T019 | REDテストを読む | ✅ ph2-test.md を確認 |
| T020 | ExclusionPattern 実装 | ✅ frozen dataclass として実装 |
| T021 | HeadingAnalysis 実装 | ✅ frozen dataclass として実装 |
| T022 | デフォルトパターン定義 | ✅ running-head, page-number 追加 |
| T023 | analyze_headings 関数 | ✅ heading頻度分析実装 |
| T024 | detect_running_head 関数 | ✅ 柱検出（閾値50%）実装 |
| T025 | reassign_heading_level 関数 | ✅ level再配置実装 |
| T026 | match_exclusion_pattern 関数 | ✅ パターンマッチング実装 |
| T027 | transform_heading 拡張 | ✅ readAloud属性出力実装 |
| T028 | コンポーネント統合 | ✅ 全コンポーネント結合確認 |
| T029 | make test PASS (GREEN) | ✅ 全340テストPASS |
| T030 | リグレッション確認 | ✅ 既存292テスト + 新規47テスト |

## 作成/修正ファイル

### 修正したファイル

#### `src/book_converter/models.py`
- ExclusionPattern dataclass を追加
  - id, priority, pattern, pattern_type, description フィールド
  - frozen=True でイミュータブル
- HeadingAnalysis dataclass を追加
  - text, level, count, levels, is_running_head フィールド
  - frozen=True でイミュータブル

#### `src/book_converter/config.py`
- DEFAULT_EXCLUSION_PATTERNS リストを追加
  - running-head (dynamic, priority=100)
  - page-number (static, pattern=`.*[―—]\s*\d+\s*/\s*\d+$`, priority=90)

#### `src/book_converter/analyzer.py`
- `analyze_headings(headings)` 関数を実装
  - heading頻度分析
  - テキストごとの出現回数、出現レベルを集計
  - HeadingAnalysis リストを返す
- `detect_running_head(analyses, total_pages)` 関数を実装
  - level=1 のみを柱候補とする
  - 出現率50%以上で柱判定
  - is_running_head フラグを更新
- `match_exclusion_pattern(text)` 関数を実装
  - 正規表現パターンマッチング
  - page-number パターン（全角ダッシュ・横棒対応）
- `reassign_heading_level(heading, running_head_texts)` 関数を実装
  - 柱テキストが level 2,3 で出現 → level 1 に再配置
  - 新しい Heading オブジェクトを返す（イミュータブル）
- `apply_read_aloud_rules(headings, analyses)` 関数を実装
  - 柱または除外パターンマッチで readAloud=False 付与
  - 新しい Heading リストを返す

#### `src/book_converter/transformer.py`
- `transform_heading(heading)` 関数を拡張
  - `heading.read_aloud=False` の場合 `readAloud="false"` 属性出力
  - `heading.read_aloud=True` の場合は属性省略（デフォルト値）
- `transform_content(content)` 内のHeading処理を拡張
  - Content内のHeadingにも同様にreadAloud属性を出力

#### `specs/003-heading-readaloud-rules/tasks.md`
- T019-T030 を [x] に更新

## テスト結果

```
============================= test session starts ==============================
collected 340 items

tests/book_converter/test_analyzer.py::TestAnalyzeHeadings .......... [ 100%]
tests/book_converter/test_analyzer.py::TestDetectRunningHead ........ [ 100%]
tests/book_converter/test_analyzer.py::TestMatchExclusionPattern ... [ 100%]
tests/book_converter/test_analyzer.py::TestReassignHeadingLevel .... [ 100%]
tests/book_converter/test_analyzer.py::TestHeadingAnalysisIntegration [ 100%]
tests/book_converter/test_models.py::TestExclusionPattern .......... [ 100%]
tests/book_converter/test_models.py::TestHeadingAnalysis ........... [ 100%]
tests/book_converter/test_transformer.py::TestHeadingReadAloudAttribute [ 100%]

============================= 340 passed in 0.72s ===============================
```

**全テスト結果**: 340 passed (既存 292 + 新規 47 + 統合1)
**リグレッション**: なし

## 実装詳細

### Constitution準拠

- **イミュータブル**: ExclusionPattern, HeadingAnalysis は frozen dataclass
- **関数型**: すべての関数は新しいオブジェクトを返し、引数を変更しない
- **型安全**: すべての関数に型ヒント付与

### アルゴリズム

#### 柱検出
1. heading頻度分析（analyze_headings）
   - テキストごとの出現回数、出現レベルを集計
   - 最頻出レベルを決定
2. 柱判定（detect_running_head）
   - level=1 のみを柱候補とする
   - 出現率 ≥ 50% で柱判定
   - 最頻出の level=1 heading を柱として検出

#### パターンマッチング
- 正規表現ベース（`re.match`）
- 優先度順にパターンをチェック
- page-number: `.*[―—]\s*\d+\s*/\s*\d+$` （全角ダッシュ・横棒対応）

#### readAloud属性付与
1. 柱として検出 → readAloud=False
2. 除外パターンマッチ → readAloud=False
3. それ以外 → readAloud=True（デフォルト、属性省略）

### XML出力例

```xml
<!-- 柱（readAloud="false"） -->
<heading level="1" readAloud="false">SREの知識地図</heading>

<!-- ページ番号表記（readAloud="false"） -->
<heading level="3" readAloud="false">1.1.1 SREの概要 — 1 / 3</heading>

<!-- 通常見出し（readAloud属性省略） -->
<heading level="2">3.2.1 モニタリングの基本</heading>
```

## 次フェーズへの引き継ぎ事項

### Phase 3（User Story 2: 装飾・区切り記号の除外）への入力

1. **既存のパターン**:
   - running-head (dynamic)
   - page-number (static)

2. **追加予定のパターン**:
   - decoration: `^[◆◇■□●○▲△]+$`
   - section-label: `^Section\s+\d+\.\d+$`

3. **実装済みコンポーネント**:
   - `match_exclusion_pattern`: 新規パターン追加のみで対応可能
   - `apply_read_aloud_rules`: 変更不要
   - `config.py`: DEFAULT_EXCLUSION_PATTERNS にパターン追加するだけ

4. **テスト戦略**:
   - Phase 3 でも同じTDDフローを使用
   - 既存の統合テストでリグレッション確認

## 計画からの逸脱

なし。すべてのタスクを計画通り完了。

## 発見事項

1. **transform_content内のHeading処理**:
   - transform_heading関数だけでなく、transform_content内のHeading処理も拡張が必要
   - test_heading_read_aloud_false_in_content テストで確認

2. **最頻出レベル決定ロジック**:
   - 同数の場合は小さいlevel優先
   - `max(data["level_counts"].items(), key=lambda x: (x[1], -x[0]))`

3. **パターンマッチング優先度**:
   - 現在は優先度順にチェック
   - dynamic タイプは match_exclusion_pattern では処理しない
   - apply_read_aloud_rules で柱検出結果を優先適用

## メトリクス

- **追加行数**: 約200行（models, config, analyzer, transformer）
- **テストカバレッジ**: 47テスト追加（境界テスト、統合テスト含む）
- **実装時間**: 約30分
- **リファクタリング**: なし（初回実装）
