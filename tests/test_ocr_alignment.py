"""Tests for OCR character-level alignment module.

Phase 3: US3 (文字レベルの投票による精度向上)

Test coverage:
- T028: align_texts_character_level - 文字レベルアライメントテスト
- T029: weighted_vote_character - 重み付き投票テスト
- T030: vote_aligned_text - アライメント統合テスト
"""

from __future__ import annotations

import pytest

from src.rover.alignment import (
    AlignedPosition,
    align_texts_character_level,
    vote_aligned_text,
    weighted_vote_character,
)

# =============================================================================
# T028: 文字レベルアライメントテスト (align_texts_character_level)
# =============================================================================


class TestAlignTextsCharacterLevel:
    """Test align_texts_character_level function for multi-text alignment."""

    def test_align_two_identical_texts(self):
        """同一テキスト2つのアライメント"""
        texts = {
            "yomitoku": "ソフトウェア",
            "paddleocr": "ソフトウェア",
        }
        result = align_texts_character_level(texts)

        # 6文字 = 6ポジション
        assert len(result) == 6
        # 各ポジションで両エンジンが同じ文字
        for i, pos in enumerate(result):
            assert pos.candidates["yomitoku"] == "ソフトウェア"[i]
            assert pos.candidates["paddleocr"] == "ソフトウェア"[i]

    def test_align_two_texts_with_one_char_difference(self):
        """1文字異なる2テキストのアライメント (ェ vs エ)"""
        texts = {
            "yomitoku": "ソフトウェア",  # 正しい表記
            "paddleocr": "ソフトウエア",  # エ と ェ が異なる
        }
        result = align_texts_character_level(texts)

        # 6文字分のポジション
        assert len(result) == 6
        # 位置4で差異がある (index 4: ェ vs エ)
        pos4 = result[4]
        assert pos4.candidates.get("yomitoku") == "ェ"
        assert pos4.candidates.get("paddleocr") == "エ"

    def test_align_three_texts(self):
        """3テキストのアライメント"""
        texts = {
            "yomitoku": "ソフトウェア",
            "paddleocr": "ソフトウエア",
            "easyocr": "ソフトウェア",
        }
        result = align_texts_character_level(texts)

        assert len(result) == 6
        # 位置4で投票の決め手になる
        pos4 = result[4]
        assert pos4.candidates.get("yomitoku") == "ェ"
        assert pos4.candidates.get("paddleocr") == "エ"
        assert pos4.candidates.get("easyocr") == "ェ"

    def test_align_with_gap_shorter_text(self):
        """短いテキストを含むアライメント (ギャップ発生)"""
        texts = {
            "yomitoku": "チーム開発",  # 5文字
            "paddleocr": "チム開発",  # 4文字 (ー が欠損)
        }
        result = align_texts_character_level(texts)

        # 長い方(5文字)に合わせてポジションが作成される
        assert len(result) == 5
        # paddleocrは位置1でギャップ(None)になるか、異なる文字になる
        # difflibの挙動により、最適なアライメントが選ばれる

    def test_align_with_gap_missing_chars(self):
        """複数文字が欠損しているテキストのアライメント"""
        texts = {
            "yomitoku": "全部入りソフトウェア",  # 10文字
            "paddleocr": "全部入りソウ",  # 6文字 (フト と ェア が欠損)
        }
        result = align_texts_character_level(texts)

        # 長い方に合わせる
        assert len(result) >= 6
        # 欠損部分はNoneで表現される

    def test_align_empty_texts(self):
        """空のテキスト辞書は空リストを返す"""
        texts = {}
        result = align_texts_character_level(texts)

        assert result == []

    def test_align_single_engine(self):
        """単一エンジンのテキストはそのままポジションリストに"""
        texts = {
            "yomitoku": "テスト",
        }
        result = align_texts_character_level(texts)

        assert len(result) == 3
        assert result[0].candidates["yomitoku"] == "テ"
        assert result[1].candidates["yomitoku"] == "ス"
        assert result[2].candidates["yomitoku"] == "ト"

    def test_align_with_empty_string(self):
        """空文字列を含む場合"""
        texts = {
            "yomitoku": "テスト",
            "paddleocr": "",
        }
        result = align_texts_character_level(texts)

        # yomitokuの3文字分
        assert len(result) == 3
        # paddleocrは全ポジションでNone
        for pos in result:
            assert pos.candidates.get("yomitoku") == pos.candidates.get("yomitoku")
            assert pos.candidates.get("paddleocr") is None

    def test_align_real_world_scenario(self):
        """実際のOCR出力に近いシナリオ"""
        # spec.mdの例: 「進捗会議」の認識差異
        texts = {
            "yomitoku": "アクションしない「聞くだけ進捗会議」",
            "paddleocr": "アクションしない「聞くだけ進会議」",  # 捗 が欠損
            "easyocr": "アクションしない「聞くだけ進排会議」",  # 捗 が 排 に誤認識
        }
        result = align_texts_character_level(texts)

        # アライメントが正しく行われる
        assert len(result) > 0
        # 各ポジションにcandidatesが存在
        for pos in result:
            assert isinstance(pos.candidates, dict)

    def test_align_returns_aligned_position_objects(self):
        """戻り値がAlignedPositionオブジェクトのリストである"""
        texts = {
            "yomitoku": "AB",
        }
        result = align_texts_character_level(texts)

        assert all(isinstance(pos, AlignedPosition) for pos in result)
        # positionフィールドが連番
        for i, pos in enumerate(result):
            assert pos.position == i


# =============================================================================
# T029: 重み付き投票テスト (weighted_vote_character)
# =============================================================================


class TestWeightedVoteCharacter:
    """Test weighted_vote_character function for single position voting."""

    def test_vote_unanimous_agreement(self):
        """全員一致の場合、その文字が採用される"""
        candidates = {
            "yomitoku": "ェ",
            "paddleocr": "ェ",
            "easyocr": "ェ",
        }
        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.95,
            "easyocr": 0.8,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        char, weight = weighted_vote_character(candidates, confidences, engine_weights)

        assert char == "ェ"
        # 全員一致なので重みは合計
        expected_weight = (1.5 * 0.9) + (1.2 * 0.95) + (1.0 * 0.8)
        assert weight == pytest.approx(expected_weight, abs=0.01)

    def test_vote_majority_two_vs_one(self):
        """2対1の場合、多数派が採用される"""
        candidates = {
            "yomitoku": "ェ",
            "paddleocr": "エ",
            "easyocr": "ェ",
        }
        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.9,
            "easyocr": 0.9,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        char, weight = weighted_vote_character(candidates, confidences, engine_weights)

        # ェ: yomitoku(1.5*0.9) + easyocr(1.0*0.9) = 2.25
        # エ: paddleocr(1.2*0.9) = 1.08
        assert char == "ェ"

    def test_vote_weight_reversal(self):
        """重み付きで逆転するケース"""
        candidates = {
            "yomitoku": "ェ",  # 重み高いが信頼度低い
            "paddleocr": "エ",
            "easyocr": "エ",
        }
        confidences = {
            "yomitoku": 0.3,  # 低信頼度
            "paddleocr": 0.95,
            "easyocr": 0.95,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        char, weight = weighted_vote_character(candidates, confidences, engine_weights)

        # ェ: 1.5*0.3 = 0.45
        # エ: 1.2*0.95 + 1.0*0.95 = 2.09
        assert char == "エ"

    def test_vote_with_none_candidates(self):
        """Noneを含む候補の場合、None以外から選択"""
        candidates = {
            "yomitoku": "ェ",
            "paddleocr": None,  # ギャップ
            "easyocr": "ェ",
        }
        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.0,
            "easyocr": 0.8,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        char, weight = weighted_vote_character(candidates, confidences, engine_weights)

        assert char == "ェ"
        # Noneは投票に参加しない
        expected_weight = (1.5 * 0.9) + (1.0 * 0.8)
        assert weight == pytest.approx(expected_weight, abs=0.01)

    def test_vote_all_none(self):
        """全てNoneの場合は空文字を返す"""
        candidates = {
            "yomitoku": None,
            "paddleocr": None,
            "easyocr": None,
        }
        confidences = {
            "yomitoku": 0.0,
            "paddleocr": 0.0,
            "easyocr": 0.0,
        }

        char, weight = weighted_vote_character(candidates, confidences)

        assert char == ""
        assert weight == 0.0

    def test_vote_default_engine_weights(self):
        """engine_weightsがNoneの場合はデフォルト重みを使用"""
        candidates = {
            "yomitoku": "ェ",
            "paddleocr": "エ",
        }
        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.9,
        }

        char, weight = weighted_vote_character(candidates, confidences, None)

        # デフォルト重み(1.5, 1.2)が適用される
        # ェ: 1.5*0.9 = 1.35 > エ: 1.2*0.9 = 1.08
        assert char == "ェ"

    def test_vote_empty_candidates(self):
        """空の候補辞書は空文字を返す"""
        candidates = {}
        confidences = {}

        char, weight = weighted_vote_character(candidates, confidences)

        assert char == ""
        assert weight == 0.0

    def test_vote_single_candidate(self):
        """単一候補はそのまま採用"""
        candidates = {
            "yomitoku": "テ",
        }
        confidences = {
            "yomitoku": 0.9,
        }
        engine_weights = {
            "yomitoku": 1.5,
        }

        char, weight = weighted_vote_character(candidates, confidences, engine_weights)

        assert char == "テ"
        assert weight == pytest.approx(1.5 * 0.9, abs=0.01)

    def test_vote_tie_breaker(self):
        """同点の場合の動作（決定的であること）"""
        candidates = {
            "yomitoku": "A",
            "paddleocr": "B",
        }
        confidences = {
            "yomitoku": 1.0,
            "paddleocr": 1.0,
        }
        engine_weights = {
            "yomitoku": 1.0,
            "paddleocr": 1.0,
        }

        # 同じ入力で同じ結果を返すこと（決定的）
        results = [weighted_vote_character(candidates, confidences, engine_weights) for _ in range(10)]
        assert all(r[0] == results[0][0] for r in results)


# =============================================================================
# T030: アライメント統合テスト (vote_aligned_text)
# =============================================================================


class TestVoteAlignedText:
    """Test vote_aligned_text function for full text voting."""

    def test_vote_software_vs_sofutowea(self):
        """「ソフトウェア」vs「ソフトウエア」の投票"""
        # 3エンジン中2エンジンが「ェ」を出力
        # yomitoku: ソフトウェア (正しい)
        # paddleocr: ソフトウエア (誤り)
        # easyocr: ソフトウェア (正しい)
        texts = {
            "yomitoku": "ソフトウェア",
            "paddleocr": "ソフトウエア",
            "easyocr": "ソフトウェア",
        }

        # まずアライメント
        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.98,
            "paddleocr": 0.90,
            "easyocr": 0.60,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        voted_text, avg_confidence = vote_aligned_text(aligned, confidences, engine_weights)

        # 多数決で「ソフトウェア」が採用される
        assert voted_text == "ソフトウェア"
        assert avg_confidence > 0

    def test_vote_all_same_text(self):
        """全エンジンが同じテキストの場合"""
        texts = {
            "yomitoku": "チーム開発",
            "paddleocr": "チーム開発",
            "easyocr": "チーム開発",
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.95,
            "paddleocr": 0.92,
            "easyocr": 0.85,
        }

        voted_text, avg_confidence = vote_aligned_text(aligned, confidences)

        assert voted_text == "チーム開発"

    def test_vote_with_gaps(self):
        """ギャップを含むテキストの投票"""
        texts = {
            "yomitoku": "チーム開発",  # 完全
            "paddleocr": "チム開発",  # 「ー」欠損
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.95,
        }
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
        }

        voted_text, _ = vote_aligned_text(aligned, confidences, engine_weights)

        # yomitokuの重みが高いので「チーム開発」が採用される
        assert "チ" in voted_text
        assert "開発" in voted_text

    def test_vote_empty_aligned_positions(self):
        """空のAlignedPositionsリストは空文字を返す"""
        aligned: list[AlignedPosition] = []
        confidences = {}

        voted_text, avg_confidence = vote_aligned_text(aligned, confidences)

        assert voted_text == ""
        assert avg_confidence == 0.0

    def test_vote_single_character_text(self):
        """1文字テキストの投票"""
        texts = {
            "yomitoku": "A",
            "paddleocr": "B",
            "easyocr": "A",
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.9,
            "easyocr": 0.9,
        }

        voted_text, _ = vote_aligned_text(aligned, confidences)

        # 2対1でAが勝つ
        assert voted_text == "A"

    def test_vote_returns_confidence(self):
        """平均信頼度が正しく計算される"""
        texts = {
            "yomitoku": "AB",
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.8,
        }
        engine_weights = {
            "yomitoku": 1.5,
        }

        voted_text, avg_confidence = vote_aligned_text(aligned, confidences, engine_weights)

        assert voted_text == "AB"
        assert avg_confidence > 0

    def test_vote_long_text(self):
        """長いテキストの投票"""
        base_text = "機能盛りすぎ「全部入りソフトウェア」"
        texts = {
            "yomitoku": base_text,
            "paddleocr": base_text,
            "easyocr": base_text,
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.95,
            "paddleocr": 0.90,
            "easyocr": 0.85,
        }

        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert voted_text == base_text

    def test_vote_preserves_special_characters(self):
        """特殊文字（括弧、記号）が保持される"""
        texts = {
            "yomitoku": "「聞くだけ進捗会議」",
            "paddleocr": "「聞くだけ進捗会議」",
        }

        aligned = align_texts_character_level(texts)

        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.9,
        }

        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert voted_text.startswith("「")
        assert voted_text.endswith("」")


# =============================================================================
# AlignedPosition データクラステスト
# =============================================================================


class TestAlignedPosition:
    """Test AlignedPosition dataclass."""

    def test_aligned_position_creation(self):
        """AlignedPositionオブジェクトの作成"""
        pos = AlignedPosition(
            position=0,
            candidates={"yomitoku": "ェ", "paddleocr": "エ"},
            confidences={"yomitoku": 0.9, "paddleocr": 0.95},
        )

        assert pos.position == 0
        assert pos.candidates["yomitoku"] == "ェ"
        assert pos.confidences["yomitoku"] == 0.9
        assert pos.voted_char == ""  # デフォルト
        assert pos.vote_weight == 0.0  # デフォルト

    def test_aligned_position_vote_method(self):
        """AlignedPosition.vote()メソッドのテスト"""
        pos = AlignedPosition(
            position=0,
            candidates={"yomitoku": "ェ", "paddleocr": "エ", "easyocr": "ェ"},
            confidences={"yomitoku": 0.9, "paddleocr": 0.9, "easyocr": 0.9},
        )
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

        result = pos.vote(engine_weights)

        assert result == "ェ"
        assert pos.voted_char == "ェ"
        assert pos.vote_weight > 0

    def test_aligned_position_vote_updates_state(self):
        """vote()呼び出し後にvoted_charとvote_weightが更新される"""
        pos = AlignedPosition(
            position=0,
            candidates={"yomitoku": "A"},
            confidences={"yomitoku": 0.8},
        )
        engine_weights = {"yomitoku": 1.5}

        pos.vote(engine_weights)

        assert pos.voted_char == "A"
        assert pos.vote_weight == pytest.approx(1.5 * 0.8, abs=0.01)


# =============================================================================
# エッジケース
# =============================================================================


class TestAlignmentEdgeCases:
    """Edge cases for character-level alignment and voting."""

    def test_unicode_characters(self):
        """Unicode特殊文字を含むテキストのアライメント"""
        texts = {
            "yomitoku": "エンジニア必読!",
            "paddleocr": "エンジニア必読!",
        }

        aligned = align_texts_character_level(texts)
        confidences = {"yomitoku": 0.9, "paddleocr": 0.9}

        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert voted_text == "エンジニア必読!"

    def test_mixed_japanese_ascii(self):
        """日本語とASCIIの混合テキスト"""
        texts = {
            "yomitoku": "SHOEISHA出版",
            "paddleocr": "SHOEISHA出版",
            "easyocr": "SHOEISHA出版",
        }

        aligned = align_texts_character_level(texts)
        confidences = {
            "yomitoku": 0.9,
            "paddleocr": 0.9,
            "easyocr": 0.9,
        }

        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert voted_text == "SHOEISHA出版"

    def test_very_different_texts(self):
        """大きく異なるテキストのアライメント"""
        texts = {
            "yomitoku": "チーム開発",
            "paddleocr": "失敗事例",
        }

        # アライメントは行われるべき（エラーにならない）
        aligned = align_texts_character_level(texts)
        confidences = {"yomitoku": 0.9, "paddleocr": 0.9}

        # 結果は何らかのテキストになる
        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert isinstance(voted_text, str)

    def test_numbers_and_symbols(self):
        """数字と記号を含むテキスト"""
        texts = {
            "yomitoku": "42の失敗事例",
            "paddleocr": "42の失敗事例",
        }

        aligned = align_texts_character_level(texts)
        confidences = {"yomitoku": 0.9, "paddleocr": 0.9}

        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert voted_text == "42の失敗事例"

    def test_whitespace_handling(self):
        """空白文字を含むテキストの処理"""
        texts = {
            "yomitoku": "チーム 開発",  # スペースあり
            "paddleocr": "チーム開発",  # スペースなし
        }

        aligned = align_texts_character_level(texts)
        confidences = {"yomitoku": 0.9, "paddleocr": 0.95}

        # アライメントとvoteが正常に動作
        voted_text, _ = vote_aligned_text(aligned, confidences)

        assert isinstance(voted_text, str)
        assert len(voted_text) > 0
