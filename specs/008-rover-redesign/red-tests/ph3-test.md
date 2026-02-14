# Phase 3 テスト実装 (RED) 出力

**日付**: 2026-02-14
**フェーズ**: Phase 3 - US3 (文字レベルの投票による精度向上)
**ステータス**: RED (FAIL) 確認済み

## サマリー

| 項目 | 値 |
|------|-----|
| 対象フェーズ | Phase 3 |
| ユーザーストーリー | US3: 文字レベルの投票による精度向上 |
| FAILテスト数 | 41件 |
| PASSテスト数 | 1件 (AlignedPositionデータクラス作成のみ) |
| 新規テストファイル | tests/test_ocr_alignment.py |
| 更新テストファイル | tests/test_ocr_rover.py |

## テストファイル一覧

| ファイル | テストクラス数 | テスト数 | 状態 |
|----------|---------------|----------|------|
| tests/test_ocr_alignment.py | 5 | 35 | FAIL (34), PASS (1) |
| tests/test_ocr_rover.py (追加分) | 1 | 7 | FAIL (7) |

## FAILテスト一覧

### tests/test_ocr_alignment.py

#### TestAlignTextsCharacterLevel (10件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_align_two_identical_texts | 同一テキスト2つを6ポジションにアライメント | NotImplementedError |
| test_align_two_texts_with_one_char_difference | 1文字異なる (ェ vs エ) を検出 | NotImplementedError |
| test_align_three_texts | 3エンジンのテキストをアライメント | NotImplementedError |
| test_align_with_gap_shorter_text | 短いテキスト (ギャップ) を処理 | NotImplementedError |
| test_align_with_gap_missing_chars | 複数文字欠損をアライメント | NotImplementedError |
| test_align_empty_texts | 空辞書で空リスト返却 | NotImplementedError |
| test_align_single_engine | 単一エンジンをそのままリスト化 | NotImplementedError |
| test_align_with_empty_string | 空文字列を含む場合のNone処理 | NotImplementedError |
| test_align_real_world_scenario | 実際のOCR出力シナリオ | NotImplementedError |
| test_align_returns_aligned_position_objects | AlignedPositionオブジェクト返却 | NotImplementedError |

#### TestWeightedVoteCharacter (9件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_vote_unanimous_agreement | 全員一致でその文字を採用 | NotImplementedError |
| test_vote_majority_two_vs_one | 2対1で多数派を採用 | NotImplementedError |
| test_vote_weight_reversal | 重み付きで逆転するケース | NotImplementedError |
| test_vote_with_none_candidates | None (ギャップ) を除外して投票 | NotImplementedError |
| test_vote_all_none | 全てNoneで空文字を返す | NotImplementedError |
| test_vote_default_engine_weights | デフォルト重みを使用 | NotImplementedError |
| test_vote_empty_candidates | 空辞書で空文字を返す | NotImplementedError |
| test_vote_single_candidate | 単一候補をそのまま採用 | NotImplementedError |
| test_vote_tie_breaker | 同点時の決定的動作 | NotImplementedError |

#### TestVoteAlignedText (8件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_vote_software_vs_sofutowea | 「ソフトウェア」vs「ソフトウエア」→「ソフトウェア」 | NotImplementedError |
| test_vote_all_same_text | 全エンジン一致でそのテキスト | NotImplementedError |
| test_vote_with_gaps | ギャップを含むテキストの投票 | NotImplementedError |
| test_vote_empty_aligned_positions | 空リストで空文字を返す | NotImplementedError |
| test_vote_single_character_text | 1文字テキストの投票 | NotImplementedError |
| test_vote_returns_confidence | 平均信頼度を計算 | NotImplementedError |
| test_vote_long_text | 長いテキストの投票 | NotImplementedError |
| test_vote_preserves_special_characters | 特殊文字 (括弧、記号) の保持 | NotImplementedError |

#### TestAlignedPosition (2件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_aligned_position_creation | データクラス作成 | **PASS** |
| test_aligned_position_vote_method | vote()メソッドの動作 | NotImplementedError |
| test_aligned_position_vote_updates_state | vote()後の状態更新 | NotImplementedError |

#### TestAlignmentEdgeCases (5件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_unicode_characters | Unicode特殊文字の処理 | NotImplementedError |
| test_mixed_japanese_ascii | 日本語とASCII混合 | NotImplementedError |
| test_very_different_texts | 大きく異なるテキスト | NotImplementedError |
| test_numbers_and_symbols | 数字と記号の処理 | NotImplementedError |
| test_whitespace_handling | 空白文字の処理 | NotImplementedError |

### tests/test_ocr_rover.py (追加分)

#### TestVoteLineTextCharacterLevel (7件)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|----------|----------|
| test_vote_line_text_character_level_software | 「ソフトウェア」vs「ソフトウエア」の文字レベル投票 | 戻り値が2つ (3つ必要) |
| test_vote_line_text_character_level_returns_three_values | 3つの値を返す (text, engines, confidence) | 戻り値が2つ |
| test_vote_line_text_character_level_with_normalized_confidence | 正規化信頼度を投票重みとして使用 | 戻り値が2つ |
| test_vote_line_text_character_level_single_engine | 単一エンジンはそのまま採用 | 戻り値が2つ |
| test_vote_line_text_character_level_partial_match | 部分一致テキストの文字レベル投票 | 戻り値が2つ |
| test_vote_line_text_character_level_empty_lines | 全行Noneで空を返す | 戻り値が2つ |
| test_vote_line_text_character_level_all_agree | 全エンジン一致の場合 | 戻り値が2つ |

## 実装ヒント

### 1. align_texts_character_level (src/ocr_alignment.py)

```python
from difflib import SequenceMatcher

def align_texts_character_level(texts: dict[str, str]) -> list[AlignedPosition]:
    """
    アルゴリズム:
    1. 最長テキストをベースとして選択
    2. 各テキストをベースとSequenceMatcherでアライメント
    3. アライメント結果を統合してAlignedPositionリストを作成

    ポイント:
    - SequenceMatcher.get_opcodes()を使用
    - 'equal', 'replace', 'insert', 'delete'のopcodesを処理
    - None = ギャップ (そのエンジンにはその位置の文字がない)
    """
```

### 2. weighted_vote_character (src/ocr_alignment.py)

```python
def weighted_vote_character(
    candidates: dict[str, str | None],
    confidences: dict[str, float],
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """
    投票計算:
    weight = engine_weights[engine] * confidences[engine]
    votes[char] += weight

    デフォルト重み:
    - yomitoku: 1.5
    - paddleocr: 1.2
    - easyocr: 1.0

    注意:
    - Noneは投票に参加しない
    - 空辞書は ("", 0.0) を返す
    """
```

### 3. vote_aligned_text (src/ocr_alignment.py)

```python
def vote_aligned_text(
    aligned_positions: list[AlignedPosition],
    confidences: dict[str, float],
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """
    全ポジションを投票で統合:
    1. 各ポジションでweighted_vote_characterを呼ぶ
    2. 投票結果の文字を連結
    3. 平均信頼度を計算
    """
```

### 4. vote_line_text更新 (src/ocr_rover.py)

```python
def vote_line_text(
    aligned_line: AlignedLine,
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, list[str], float]:  # 3つの値を返す
    """
    Phase 3で更新:
    - 行レベル投票 → 文字レベル投票
    - align_texts_character_level + vote_aligned_text を使用
    - 戻り値: (voted_text, source_engines, final_confidence)
    """
```

## FAIL出力例

```
tests/test_ocr_alignment.py::TestAlignTextsCharacterLevel::test_align_two_identical_texts FAILED

    def test_align_two_identical_texts(self):
        texts = {
            "yomitoku": "ソフトウェア",
            "paddleocr": "ソフトウェア",
        }
>       result = align_texts_character_level(texts)
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests/test_ocr_alignment.py:37:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

texts = {'paddleocr': 'ソフトウェア', 'yomitoku': 'ソフトウェア'}

    def align_texts_character_level(
        texts: dict[str, str],
    ) -> list[AlignedPosition]:
        # TODO: Implement in Phase 3 (US3)
>       raise NotImplementedError("align_texts_character_level not yet implemented")
E       NotImplementedError: align_texts_character_level not yet implemented

src/ocr_alignment.py:52: NotImplementedError
```

## 次のステップ

1. **Implementation (GREEN)** フェーズへ進む
2. 以下の関数を実装:
   - `AlignedPosition.vote()` メソッド
   - `align_texts_character_level()` 関数
   - `weighted_vote_character()` 関数
   - `vote_aligned_text()` 関数
   - `vote_line_text()` 関数の更新 (3つの値を返す)
3. `make test` で全テストPASSを確認
