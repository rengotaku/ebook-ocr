# Feature Specification: ROVER OCR再設計

**Feature Branch**: `008-rover-redesign`
**Created**: 2026-02-14
**Status**: Draft
**Input**: User description: "roverの再設計"

## 背景と問題

### 現状の問題点

1. **行レベルのみの投票**: 現在の実装は行全体を比較し、類似度80%以上で「同じ」と判定している。文字レベルの補完ができていない。
2. **信頼度計算の欠陥**: エンジン固有のconfidenceが取得できておらず、常に1.0が使用されている。
3. **ゴミフィルタなし**: Tesseractの断片的出力（EE, HS等）がそのまま投票に参加している。
4. **本来のROVERとの乖離**: 文字/単語レベルのアライメントと投票が行われていない。

### 期待される動作

本来のROVER (Recognizer Output Voting Error Reduction) は：
- 複数の認識結果を文字/単語レベルでアライメント
- 各位置で多数決投票
- 欠損を他エンジンから補完

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基本的なOCR補完 (Priority: P1)

ユーザーは、yomitokuで欠損した文字列を他のOCRエンジン（PaddleOCR、EasyOCR）から補完したい。例えば、yomitokuが「チーム開発」を認識できなかった場合、PaddleOCRの「チム開発」やEasyOCRの「チーム開発」から正しいテキストを復元する。

**Why this priority**: OCR欠損補完はROVERの最も基本的な価値提供であり、これがなければ単一エンジン使用と変わらない。

**Independent Test**: 意図的に欠損を含むyomitoku出力と、完全な出力を持つ他エンジンの結果を入力し、補完結果が正しいことを確認できる。

**Acceptance Scenarios**:

1. **Given** yomitokuで「第三章」が欠損、PaddleOCRで「第三章」が認識されている, **When** ROVER処理を実行, **Then** 最終出力に「第三章」が含まれる
2. **Given** yomitokuで「アルゴリズムの」が欠損、PaddleOCRで「アルゴリズムの計算量」が認識されている, **When** ROVER処理を実行, **Then** 欠損部分が補完される
3. **Given** 全エンジンで同じテキストが認識されている, **When** ROVER処理を実行, **Then** そのテキストがそのまま出力される

---

### User Story 2 - ゴミ出力の除外 (Priority: P1)

ユーザーは、Tesseract等の低品質エンジンが出力するゴミ文字列（意味のない英字の断片、繰り返し文字等）が最終結果に混入しないことを期待する。

**Why this priority**: ゴミ混入は補完の意味を失わせるため、基本機能として必須。

**Independent Test**: Tesseractからの断片的出力（「EE」「HS」「YR」等）を含む入力で、最終出力にこれらが含まれないことを確認。

**Acceptance Scenarios**:

1. **Given** Tesseractが「EE」「HS」等の短いASCII断片を出力, **When** ROVER処理を実行, **Then** これらは最終出力に含まれない
2. **Given** 同じ文字が5回以上繰り返される出力がある, **When** ROVER処理を実行, **Then** その出力は無視される
3. **Given** 日本語文字を含まない短い出力がある, **When** ROVER処理を実行, **Then** その出力は投票から除外される

---

### User Story 3 - 文字レベルの投票による精度向上 (Priority: P2)

ユーザーは、複数エンジンの出力を文字レベルで比較し、最も信頼性の高い結果を得たい。例えば「全部入りソフトウェア」vs「全部入りソウ」の場合、より多くのエンジンが認識した文字を採用する。

**Why this priority**: 行レベル投票では部分的な誤りを修正できないため、精度向上に必要。

**Independent Test**: 部分的に異なる複数エンジンの出力を入力し、多数決で正しい文字が採用されることを確認。

**Acceptance Scenarios**:

1. **Given** yomitokuが「ソフトウェア」、PaddleOCRが「ソフトウエア」、EasyOCRが「ソフトウェア」を出力, **When** ROVER処理を実行, **Then** 多数派の「ソフトウェア」が採用される
2. **Given** 3エンジン中2エンジンが同じ文字を認識, **When** ROVER処理を実行, **Then** 多数派の文字が採用される

---

### User Story 4 - 処理前後の比較可能性 (Priority: P2)

ユーザーは、各OCRエンジンの原文出力とROVER補完後の出力を比較し、補完効果を確認したい。

**Why this priority**: 補完の透明性と検証のために必要。

**Independent Test**: 出力ディレクトリ構造を確認し、raw/とrover/の両方にファイルが存在することを確認。

**Acceptance Scenarios**:

1. **Given** ROVER処理を実行, **When** 出力ディレクトリを確認, **Then** raw/{エンジン名}/に各エンジンの原文が保存されている
2. **Given** ROVER処理を実行, **When** 出力ディレクトリを確認, **Then** rover/に補完後のテキストが保存されている

---

### Edge Cases

- 全エンジンが異なる結果を出力した場合はどうするか？→ エンジン優先度（yomitoku > paddleocr > easyocr）に従う
- 全エンジンが空の結果を返した場合は？→ 空文字列を出力
- 画像が読み込めない場合は？→ エラーをログに記録し、そのページをスキップ
- 1つのエンジンのみ成功した場合は？→ そのエンジンの結果をそのまま採用

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは複数のOCRエンジン（yomitoku、PaddleOCR、EasyOCR）の結果を受け取り、統合すること（Tesseractは除外）
- **FR-002**: システムは各エンジンの出力を行単位でグループ化し、y座標でアライメントすること
- **FR-003**: システムはアライメントされた行内で、文字レベルのアライメント（difflib.SequenceMatcher）と信頼度重み付き多数決投票を行うこと
- **FR-004**: システムはゴミ出力（日本語を含まない短い文字列、繰り返し文字等）を投票前に除外すること
- **FR-005**: システムは投票結果に基づき、各位置で最も信頼性の高いテキストを選択すること
- **FR-006**: システムはyomitokuで欠損している領域を、他エンジンの結果から補完すること
- **FR-007**: システムは各エンジンの原文出力をraw/ディレクトリに保存すること
- **FR-008**: システムはROVER補完後の出力をrover/ディレクトリに保存すること
- **FR-009**: システムはエンジン毎に重み付けを行い、yomitokuを最優先とすること

### Key Entities

- **TextWithBox**: テキストとその位置情報（bbox）、信頼度を持つ認識結果単位
- **OCRLine**: 同一行に属するTextWithBoxの集合。y座標でグループ化される
- **AlignedPosition**: 複数エンジンの結果がアライメントされた1つの位置。各エンジンの候補と投票結果を持つ
- **ROVERResult**: 最終的な補完済みテキストと、補完統計情報（補完箇所数、エンジン貢献度等）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: yomitokuで欠損した行の80%以上が、他エンジンから正しく補完されること
- **SC-002**: ゴミ出力（ASCII断片、繰り返し文字）が最終結果に混入する確率が1%未満であること
- **SC-003**: 処理時間が単一エンジン使用時の4倍を超えないこと（並列実行可能な場合は2倍以内）
- **SC-004**: raw/とrover/ディレクトリの比較により、全ての補完箇所が追跡可能であること
- **SC-005**: 文字レベル投票により、部分的な誤認識の修正率が行レベル投票比で20%以上向上すること

## Assumptions

- 入力画像は日本語書籍のスキャンまたは撮影画像である
- 主要言語は日本語であり、英語は副次的である
- 各OCRエンジンは既にインストール・設定済みである
- yomitokuが最も高品質な出力を提供するエンジンである
- 処理はCPU環境でも実行可能である必要がある

## 画像前処理

各OCRエンジンの内部前処理状況と外部前処理の方針：

| エンジン | 内部前処理 | 外部前処理 | ROVER参加 |
|----------|-----------|-----------|-----------|
| yomitoku | ✅ 充実（向き検出、歪み補正、レイアウト解析） | なし | ✅ |
| PaddleOCR | ✅ 充実（向き分類、歪み補正） | なし | ✅ |
| EasyOCR | △ 基本的 | **CLAHE適用** | ✅ |
| Tesseract | ❌ 最小限 | - | ❌ **除外** |

**Tesseract除外理由**:
- 日本語OCR精度が低い（断片化が激しい）
- 前処理しても根本的な改善が見込めない
- ROVERへの貢献度が低く、ゴミ混入リスクが高い

### EasyOCR用前処理

EasyOCRは低品質画像に弱いため、**CLAHE（Contrast Limited Adaptive Histogram Equalization）** を適用する。

```python
import cv2
import numpy as np

def preprocess_for_easyocr(image: np.ndarray) -> np.ndarray:
    """Apply CLAHE preprocessing for EasyOCR."""
    # Convert to LAB color space
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    # Convert back to RGB
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
```

## Golden Output Definition

**基準**: OCRベース（4エンジン出力の最適組み合わせが目標）

ROVERの目標品質は、利用可能なOCRエンジンの出力を最適に組み合わせた「現実的に達成可能な最高品質」とする。画像から人間が読み取れる理想的なテキストではなく、OCRエンジンが実際に出力したテキストの範囲内で最適化する。

### 達成可能性の判定基準

| 条件 | 達成可能性 |
|------|-----------|
| 2エンジン以上が同一テキストを出力 | ✅ 高（多数決で決定可能） |
| 1エンジンのみが完全な出力を持つ | ⚠️ 中（そのエンジンを採用） |
| 全エンジンが異なる部分的誤りを持つ | ⚠️ 低（文字レベル投票で補完試行） |
| 全エンジンが欠損 | ❌ 不可能（補完できない） |

### 信頼度によるフィルタリング

**閾値**: `confidence < 0.5` で除外

| エンジン | 信頼度取得方法 | 幻覚/ゴミ例 | その信頼度 |
|----------|---------------|------------|-----------|
| yomitoku | `words.rec_score` | 「美咲あ」 | 0.049 |
| easyocr | `confidence` | 「蟹」「蒼崩盛のまぎ...」 | 0.084, 0.000 |
| tesseract | `conf / 100` | 「胡」「州」「趣」 | 0.000 |
| paddleocr | `scores[i]` | - | - |

**実装方針**: yomitokuは `paragraphs` と `words` を併用する。
- **構造情報**: `paragraphs` から取得（order, role, 改行保持）
- **信頼度**: `words` から取得し、テキストまたは座標でマッチング
- paragraphsのcontentsに含まれるwordsの `rec_score` の最小値または平均値を段落の信頼度とする

**真のROVERアルゴリズム（文字レベル投票）**:

本実装は音声認識分野のROVER (Recognizer Output Voting Error Reduction) に準拠し、文字レベルでのアライメントと信頼度重み付き多数決を行う。

### アルゴリズム概要

1. **行レベルアライメント**: y座標でエンジン間の行をマッチング
2. **文字レベルアライメント**: アライメントされた行内で、各エンジンのテキストを文字単位でアライメント（difflib.SequenceMatcher使用）
3. **信頼度重み付き投票**: 各文字位置で、エンジンの信頼度を重みとして多数決
4. **ゴミフィルタ**: 投票前に低信頼度テキストを除外

### 文字レベル投票の詳細

```
# 各文字位置での投票
for position in aligned_positions:
    candidates = get_candidates_at_position(position)  # {engine: char}

    # 信頼度重み付き投票
    votes = {}
    for engine, char in candidates.items():
        weight = engine_weights[engine] * confidences[engine]
        votes[char] = votes.get(char, 0) + weight

    # 最高得票の文字を採用
    result_char = max(votes, key=votes.get)
```

### 信頼度の役割

- **投票の重み**: 各エンジンの信頼度は**正規化後**に投票の重みとして使用
- **ゴミフィルタ**: `raw_confidence < 0.5` のテキストは投票参加前に除外（正規化前の値で判定）
- **最終信頼度**: 採用された文字を出力したエンジンの正規化信頼度の加重平均

### 信頼度の正規化

各エンジンの信頼度スケールが異なるため、投票前に[0,1]に正規化する。

**実測値（page_0024での計測結果）**:

| エンジン | 取得元 | 実測範囲 | 平均 | 信頼性 |
|----------|--------|----------|------|--------|
| yomitoku | `words.rec_score` | 0.41 - 1.0 | 0.96 | ⭐⭐⭐ 最高 |
| paddleocr | `rec_scores[i]` | 0.87 - 1.0 | 0.96 | ⭐⭐⭐ 高 |
| easyocr | `confidence` | 0.26 - 1.0 | 0.80 | ⭐⭐ 中 |

**観察**:
- yomitokuとpaddleocrは常に高信頼度（ほぼ0.9以上）→ 高品質を反映
- easyocrは分布が広い（低〜高）→ 結果の信頼性にばらつきあり

**正規化関数**:

```python
def normalize_confidence(raw_conf: float, engine: str) -> float:
    """Normalize confidence to [0, 1] scale based on engine-specific range."""
    ranges = {
        "yomitoku": (0.4, 1.0),   # words.rec_score range
        "easyocr": (0.25, 1.0),   # confidence range
        "paddleocr": (0.85, 1.0), # rec_scores range (narrow)
    }
    min_conf, max_conf = ranges.get(engine, (0.0, 1.0))
    normalized = (raw_conf - min_conf) / (max_conf - min_conf)
    return max(0.0, min(1.0, normalized))
```

**投票重み計算**:

```python
# 正規化後の投票重み
weight = engine_weight * normalize_confidence(raw_conf, engine)

# 例: yomitoku raw_conf=0.9
# normalized = (0.9 - 0.4) / 0.6 = 0.833
# weight = 1.5 * 0.833 = 1.25
```

### 例: 「ソフトウェア」vs「ソフトウエア」（正規化後）

| 位置 | yomitoku (w=1.5, raw=0.99, norm=0.98) | paddle (w=1.2, raw=0.95, norm=0.90) | easy (w=1.0, raw=0.7, norm=0.60) | 投票結果 |
|------|--------------------------------------|-------------------------------------|----------------------------------|----------|
| 0 | ソ | ソ | ソ | ソ (全員一致) |
| 1 | フ | フ | フ | フ (全員一致) |
| 2 | ト | ト | ト | ト (全員一致) |
| 3 | ウ | ウ | ウ | ウ (全員一致) |
| 4 | **ェ** | **エ** | **ェ** | **ェ** (yomi:1.47 + easy:0.60 = 2.07 > paddle:1.08) |
| 5 | ア | ア | ア | ア (全員一致) |

→ 結果: 「ソフトウェア」（正しい表記が採用される）

### ゴミフィルタ（投票前）

投票に参加する前に、以下の条件でゴミ出力を除外:
- `confidence < 0.5`
- 日本語を含まない5文字以下のASCII
- 同一文字が5回以上繰り返し

### ゴールデンテストケース: page_0002

**入力**: `output/157012a97dcbebed/pages/page_0002.png`（書籍表紙）

**各エンジン出力の品質分析**:

| テキスト | yomitoku | paddle | easy | tesseract | 達成可能性 |
|----------|----------|--------|------|-----------|-----------|
| 出石聡史 | ✓ | ✓ | ✗ | ✗ | ✅ 2票 |
| 42の失敗事例で学ぶ | ✓ | ✓ | ✗ | ✗ | ✅ 2票 |
| チーム開発の | ✓ | チム | ✗ | ✗ | ⚠️ 1票のみ |
| うまい進めかた | ✓ | ✓ | ✗ | ✗ | ✅ 2票 |
| ソフトウェア | ✗ | ソフトウエア | ✓ | ✗ | ⚠️ 1票のみ |
| 開発現場の | ✗ | ✓ | ✓ | ✗ | ✅ 2票 |
| 「失敗」集め | ✗ | ✓ | ✓ | ✗ | ✅ 2票 |
| てみた。 | ✗ | てみた | ✓ | ✗ | ⚠️ 1票のみ |
| よくある落とし穴の回避策がわかる! | ✓ | ✓ | 部分 | ✗ | ✅ 2票 |
| 機能盛りすぎ「全部入りソフトウェア」 | ✓ | 欠落 | ✗ | ✗ | ⚠️ 1票のみ |
| 行間を読ませる「文学的仕様書」 | ✓ | ✓ | ✗ | ✗ | ✅ 2票 |
| アクションしない「聞くだけ進捗会議」 | ✓ | 進会議 | 進排会議 | ✗ | ⚠️ 1票のみ |
| やらかしたくないエンジニア必読! | ✓ | ✓ | ✓ | ✗ | ✅ 3票 |
| SHOEISHA | ✗ | ✓ | ✓ | ✓ | ✅ 3票 |

**除外すべき誤認識**:
- `愛媛県` (yomitoku) - 画像に存在しない幻覚
- `EEHe`, `YRHS`, `i,` など (tesseract断片) - ゴミ

## Clarifications

### Session 2026-02-14

- Q: ゴールデン出力の基準は？（OCRベース vs 画像ベース） → A: OCRベース（4エンジン出力の最適組み合わせを目標）
- Q: 幻覚テキスト（画像に存在しない日本語）の扱いは？ → A: 信頼度閾値で判定（confidence < 0.5 は除外）
- Q: yomitokuは信頼度を提供するか？ → A: `words.rec_score` で取得可能（現在の `paragraphs` ベースから `words` ベースに変更が必要）
- Q: yomitokuをwords単位にすると構造が失われないか？ → A: paragraphs + words 併用（構造はparagraphs、信頼度はwordsからマッチング）
- Q: 信頼度フィルタで正しいテキストが除外されないか？ → A: 類似テキストを出力した全エンジンの信頼度の最大値を採用（`final_conf = max(all_similar_conf)`）
- Q: OCRに読ませる画像の前処理は必要か？ → A: EasyOCR用のみCLAHE前処理を追加（yomitoku/PaddleOCRは内部処理が充実）
- Q: Tesseractは使用するか？ → A: 除外（日本語精度低、断片化激しい、ゴミ混入リスク高）
- Q: 現在の信頼度再計算（max）はROVERといえるのか？ → A: 真のROVER（文字レベルアライメント + 信頼度重み付き多数決）を採用。信頼度は投票の重みとして使用
- Q: yomitokuとeasyocrの信頼度を単純に足しても問題ないか？ → A: 問題あり。各エンジンの信頼度スケールが異なる（yomitoku: 0.4-1.0, easyocr: 0.25-1.0）ため、正規化してから加算する
- Q: paddleocrの信頼度範囲は？ → A: 0.87-1.0（平均0.96）。yomitokuと同様に高信頼度。正規化範囲は(0.85, 1.0)
