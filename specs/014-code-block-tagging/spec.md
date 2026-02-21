# Feature Specification: コードブロックタグ付け機能

**Feature Branch**: `014-code-block-tagging`
**Created**: 2026-02-20
**Status**: Draft
**Input**: GitHub Issue #16 - codeブロックタグをつける

## Clarifications

### Session 2026-02-20

- Q: コードブロック検出の入力ソースと検出アプローチは？ → A: レイアウト検出拡張（画像レベルでコード領域を視覚的に検出）
- Q: レイアウト検出拡張の具体的な実装方法は？ → A: 別モデル追加（コード領域専用の検出モデルを追加し、既存検出と組み合わせ）
- Q: コード検出の主要視覚特徴は？ → A: ハイブリッド（OpenCV枠線検出 + テキストパターン検証）。既存のDocLayNet等にはコードクラスが存在しないためカスタム実装が必要
- Q: インラインコード、言語推定のスコープは？ → A: 対象外とする（コード/非コードの二値判定のみ）
- Q: テキストパターン検証の技術は？ → A: Guesslang（TensorFlowベース、93.45%精度）。`language_name()`がNoneまたは確率が閾値未満なら非コードと判定

### Session 2026-02-21

- Q: yomitokuのTEXT領域とOpenCVコード検出領域が重複した場合の処理は？ → A: コード優先（OpenCV+Guesslangで確定したコード領域が、yomitokuのTEXT領域を上書き）
- Q: コード検出はパイプラインのどの段階で実行するか？ → A: yomitoku完了後（layout.jsonを参照してコード検出を追加実行）
- Q: layout.jsonへのコード領域記録方法は？ → A: 既存形式拡張（`type: "CODE"`, `label: "code"` を追加）
- Q: boxマージアルゴリズムは？ → A: シンプル置換（IoU > 0、少しでも重複があればTEXTを削除してCODEで置換）
- Q: コード検出モジュールの配置は？ → A: `src/layout/code_detector.py` として追加
- Q: コード検出失敗時の処理は？ → A: スキップして続行（失敗した領域はTEXTのまま維持）、ただし警告ログを出力
- Q: コードブロックの視覚特徴（枠線 vs 背景色）は？ → A: yomitoku TEXT領域 + Guesslang判定。OpenCV枠線検出は不要（yomitokuが既にTEXT領域を検出済み）
- Q: yomitokuとのマージ方式は？ → A: 既存TEXT領域の再分類（IoU計算不要）。GuesslangでコードならTEXT→CODEに`type`を変更

## User Scenarios & Testing *(mandatory)*

### User Story 1 - コードブロックの検出とタグ付け (Priority: P1)

書籍変換システムのユーザーとして、書籍画像内のコードブロックが自動的に識別され、`<code>`タグでマークアップされ、TTS読み上げから除外されることを期待する。これにより、技術書のコード部分が音声として読み上げられることなく、適切に処理される。

**Why this priority**: コードブロックはプログラミング関連書籍において頻出する要素であり、音声読み上げ（TTS）時にコードを読み上げることは聴取者にとって混乱を招く。現在のレイアウト検出はコードを「plain text」として分類してしまい、段落と区別できない。

**Independent Test**: コードブロックを含む書籍ページ画像を処理し、レイアウト検出結果に「code」領域が含まれ、最終XMLに`<code readAloud="false">`要素が生成されることを確認する。

**Acceptance Scenarios**:

1. **Given** 書籍ページ画像にコードブロックがある, **When** コード検出を実行する, **Then** 該当TEXT領域が「code」タイプとして再分類される
2. **Given** 検出された「code」領域がある, **When** 書籍変換を実行する, **Then** 出力XMLに`<code readAloud="false">`要素が生成される
3. **Given** TEXT領域のテキストがコードである, **When** Guesslangで判定する, **Then** コードとして識別される
4. **Given** TEXT領域のテキストが「コラム」等の日本語文章である, **When** Guesslangで判定する, **Then** 非コードとしてTEXTのまま維持される

---

### Edge Cases

- 空のコードブロック（枠線のみ）がある場合
  - → Guesslangで判定不能、非コードとして扱う
- コードと図が混在する領域（コード内にダイアグラムが含まれる）
  - → 図部分は`<figure>`、コード部分は`<code>`として分離を試みる
- 非常に長いコードブロック（1000行以上）がある場合
  - → 分割せず単一の`<code>`要素として処理
- Guesslangの判定確率が閾値付近の場合
  - → 設定可能な信頼度閾値を用いて判断
- 疑似コードや擬似言語の場合
  - → Guesslangがコードと判定すればコードとして扱う
- 「コラム」「Note」等の囲み記事がある場合
  - → Guesslangが非コードと判定、または日本語テキストとして除外
- OpenCV枠線検出またはGuesslang判定が失敗した場合
  - → 失敗した領域はTEXTのまま維持、警告ログを出力して続行（パイプラインは停止しない）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムはyomitokuのTEXT領域をコードブロック候補として使用しなければならない
- **FR-002**: システムは各TEXT領域のOCRテキストをGuesslangで判定し、コードか非コードかを分類しなければならない
- **FR-003**: システムは検出されたコード領域をlayout.jsonに「code」タイプとして記録しなければならない
- **FR-004**: システムは生成された`<code>`要素に`readAloud="false"`属性を自動設定しなければならない
- **FR-005**: システムはコードブロックの元のフォーマット（改行、空白、インデント）を保持しなければならない
- **FR-006**: システムはGuesslangの判定確率を信頼度として記録し、閾値による判定を可能にしなければならない

### Key Entities

- **Code**: ブロック形式のコードスニペットを表す。コード本体、readAloud属性、検出信頼度を持つ
- **CodeRegion**: レイアウト検出結果におけるコード領域。バウンディングボックス、Guesslang判定結果、信頼度を持つ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: コードブロック（Guesslangで判定）が90%以上の精度でXML `<code>`要素に変換される
- **SC-002**: 変換されたコード要素のすべてに`readAloud="false"`属性が設定される
- **SC-003**: コードブロック内の元のフォーマット（改行、インデント）が95%以上保持される
- **SC-004**: 既存の書籍変換処理のパフォーマンスが20%以上低下しない
- **SC-005**: 誤検出率（「コラム」等の非コードがコードとして検出される）が5%以下

## Assumptions

- 入力は書籍ページの画像であり、OCR処理を経てテキスト化される
- コードブロックは視覚的に区別可能な特徴を持つ（枠線またはグレー背景）
- 既存のDocLayout-YOLO/yomitokuには「code」クラスが存在しないため、Guesslang判定で補完
- **簡素化アプローチを採用**（技術検証により決定）:
  1. yomitokuのTEXT領域をそのまま使用（OpenCV枠線検出は不要）
  2. 各TEXT領域のOCRテキストにGuesslangを適用
  3. コードと判定されたらtype="CODE"に変更（IoU計算不要）
- Guesslangは93.45%の精度でコード判定が可能（54言語対応）
- Guesslangの`language_name()`がNoneを返す、または確率が閾値未満の場合は非コードと判定
- TensorFlow依存はファイルサイズ増加のみで、推論時のマシン負荷は軽微
- 既存のレイアウト検出パイプライン（yomitoku）は変更せず、コード検出結果をマージする形で統合
- **統合ポイント**: yomitoku完了後にコード検出を実行。layout.jsonのTEXT領域を走査してGuesslang判定
- **マージアルゴリズム**: 既存TEXT領域の再分類のみ（IoU計算不要）。Guesslangでコードと判定されたらtype="TEXT"→"CODE"に変更
- **layout.json形式**: 既存のregion形式を拡張（`type: "CODE"`, `label: "code"`, `bbox`, `confidence`）
- コードブロックは既存のセクション要素（Heading, Paragraph, List, Figure）と同等のレベルで処理される

## Out of Scope

- インラインコードの検出（段落内の短いコード片）
- プログラミング言語の種別判定（コード/非コードの二値判定のみ）
- コード実行や構文検証
- コードのシンタックスハイライト（TTS用途のため不要）
- コードの自動整形やフォーマット修正
- OCRエンジン自体の改修（レイアウト検出段階で対応）
- 100%の検出精度（視覚的に曖昧なケースは許容）
