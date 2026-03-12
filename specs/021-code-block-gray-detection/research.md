# Research: コードブロック視覚検出

**Date**: 2026-03-12
**Feature**: 021-code-block-gray-detection

## 調査結果

### 1. yomitoku の FIGURE 内テキスト取得方法

**Decision**: `figure.paragraphs` フィールドから取得

**Rationale**: yomitoku の `FigureSchema` は内部にパラグラフ情報を持つ。`figure.paragraphs` でテキストにアクセス可能。追加 OCR 不要。

**Alternatives considered**:
- Tesseract で FIGURE 領域に OCR 試行 → 不要（yomitoku テキストで 2,000 倍高速）
- PaddleOCR → 同上

### 2. コード判定方式

**Decision**: 記号比率 (> 0.08) + 拡張キーワード (>= 2) の OR 併用

**Rationale**: Issue #22 の検証で F1=90.2%（Java 書籍）。記号比率は言語非依存（25言語中18/25）、キーワードで残り6言語を補完。併用で24/25言語カバー。

**Alternatives considered**:
- Guesslang → 日本語書籍に不適（F1=15.6%）、Python 3.9 限定
- Tesseract + 記号比率のみ → yomitoku テキストで十分、Tesseract 追加不要
- 等幅フォント検出 → 実装複雑、日本語混在で精度不確実

### 3. 灰色背景の HSV 閾値

**Decision**: 彩度(S) < 30、明度(V) 50-200、灰色比率 ≥ 0.7

**Rationale**: feat/022 ブランチでの実装・テストで検証済み。白背景（V > 200）と黒背景（V < 50）を除外しつつ灰色を正確に検出。

**Alternatives considered**:
- RGB 平均値ベース → HSV の方がカラーと無彩色の分離が明確
- ヒストグラム分析 → 単純な画素比率で十分

### 4. アスペクト比フィルタ閾値

**Decision**: 幅/高さ > 8.0 で帯状ヘッダーと判定し除外

**Rationale**: 灰色帯ヘッダー（「リスト2.5 概念ごとに…」等）は幅1200px × 高さ40px（ratio ≈ 30）。コードブロックは幅800px × 高さ400px（ratio ≈ 2）。8.0 で安全に分離可能。

### 5. 断片結合の垂直ギャップ閾値

**Decision**: 80px

**Rationale**: Issue #22 の検証で、同一コードブロック内のパラグラフ間ギャップは数十px、本文との間は100px+。80px で安全に分離。設定ファイルで調整可能。

### 6. 拡張キーワードリスト

**Decision**: 25言語対応の多言語キーワードセット

**Rationale**: Issue #22 の検証で、記号比率のみ 18/25 言語、キーワードのみ 22/25 言語、併用で 24/25 言語をカバー。CloudFormation（純 YAML）のみ未対応。

**キーワード一覧**:

| カテゴリ | キーワード |
|---------|----------|
| General | class, void, private, public, return, throw, new, static, interface, extends, implements, var, val |
| Python | def, import, from, self., async, await, lambda, elif |
| Go | func, package, defer, := |
| Rust | fn, let, mut, impl, pub, struct, match |
| Ruby/Elixir | require, module, defmodule, rescue |
| C/C++ | #include, typedef, sizeof(, std:: |
| JS/TS | const, function, => |
| IaC/DevOps | resource ", FROM, WORKDIR, RUN, COPY, CMD [, EXPOSE, apiVersion:, kind:, spec:, hosts:, tasks: |
| SQL | SELECT, WHERE, INSERT, CREATE |
| Shell | #!/bin/, echo, ${ |

### 7. feat/022 ブランチとの関係

**Decision**: feat/022 の灰色背景検出コードを参考にしつつ、021 ブランチで最初から実装

**Rationale**: feat/022 は main にマージされていない。021 ブランチは最新 main ベースで、灰色検出 + テキスト分析 + 断片結合をまとめて実装する。feat/022 のコード・テストは設計参考として活用。
