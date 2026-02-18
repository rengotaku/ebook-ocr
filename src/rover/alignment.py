"""Character-level alignment module for ROVER OCR.

Provides character-level text alignment using difflib.SequenceMatcher
and weighted voting for the True ROVER algorithm.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class AlignedPosition:
    """Single position in character-level alignment."""

    position: int  # Position in the base text
    candidates: dict[str, str | None]  # engine -> character (None = gap)
    confidences: dict[str, float]  # engine -> confidence
    voted_char: str = ""
    vote_weight: float = 0.0

    def vote(self, engine_weights: dict[str, float]) -> str:
        """Vote for best character using weighted voting.

        Args:
            engine_weights: Weight for each engine.

        Returns:
            The winning character.
        """
        votes: dict[str, float] = {}
        for engine, char in self.candidates.items():
            if char is None:
                continue
            weight = engine_weights.get(engine, 1.0) * self.confidences.get(engine, 0.5)
            votes[char] = votes.get(char, 0.0) + weight

        if not votes:
            self.voted_char = ""
            self.vote_weight = 0.0
            return ""

        self.voted_char = max(votes, key=votes.get)
        self.vote_weight = votes[self.voted_char]
        return self.voted_char


def align_texts_character_level(
    texts: dict[str, str],
) -> list[AlignedPosition]:
    """Align multiple texts at character level using difflib.

    Args:
        texts: Dict mapping engine name to text.

    Returns:
        List of AlignedPosition objects, one per aligned position.

    Algorithm:
        1. Select longest text as base
        2. Align each other text to base using SequenceMatcher
        3. Merge alignments into unified position list
    """
    if not texts:
        return []

    # Filter out empty strings
    non_empty_texts = {eng: txt for eng, txt in texts.items() if txt}
    if not non_empty_texts:
        return []

    # Single engine case
    if len(non_empty_texts) == 1:
        engine, text = list(non_empty_texts.items())[0]
        return [
            AlignedPosition(
                position=i,
                candidates={engine: char},
                confidences={engine: 1.0},
            )
            for i, char in enumerate(text)
        ]

    # Select longest text as base
    base_engine = max(non_empty_texts.items(), key=lambda x: len(x[1]))[0]
    base_text = non_empty_texts[base_engine]

    # Initialize positions with base text
    positions: list[AlignedPosition] = [
        AlignedPosition(
            position=i,
            candidates={base_engine: char},
            confidences={base_engine: 1.0},
        )
        for i, char in enumerate(base_text)
    ]

    # Align each other text to base
    for engine, text in non_empty_texts.items():
        if engine == base_engine:
            continue

        matcher = SequenceMatcher(None, base_text, text)
        opcodes = matcher.get_opcodes()

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                # Matching characters
                for k in range(i2 - i1):
                    positions[i1 + k].candidates[engine] = text[j1 + k]
                    positions[i1 + k].confidences[engine] = 1.0
            elif tag == "replace":
                # Replacement: align position by position
                for k in range(min(i2 - i1, j2 - j1)):
                    positions[i1 + k].candidates[engine] = text[j1 + k]
                    positions[i1 + k].confidences[engine] = 1.0
                # If text is longer, remaining chars are gaps in base (ignore for now)
                # If base is longer, remaining positions get None
                for k in range(j2 - j1, i2 - i1):
                    positions[i1 + k].candidates[engine] = None
                    positions[i1 + k].confidences[engine] = 0.0
            elif tag == "delete":
                # Base has characters, other text doesn't (gap in other)
                for k in range(i2 - i1):
                    positions[i1 + k].candidates[engine] = None
                    positions[i1 + k].confidences[engine] = 0.0
            # tag == "insert": text has extra characters, base doesn't
            # These don't map to any base position, so we ignore them

    return positions


def weighted_vote_character(
    candidates: dict[str, str | None],
    confidences: dict[str, float],
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """Vote for best character at a single position.

    Args:
        candidates: Dict of engine -> character (None = gap).
        confidences: Dict of engine -> confidence.
        engine_weights: Weight for each engine.

    Returns:
        Tuple of (voted_char, vote_weight).

    Formula:
        weight = engine_weights[engine] * confidences[engine]
        votes[char] += weight
        result = max(votes, key=votes.get)
    """
    if engine_weights is None:
        engine_weights = {
            "yomitoku": 1.5,
            "paddleocr": 1.2,
            "easyocr": 1.0,
        }

    if not candidates:
        return "", 0.0

    votes: dict[str, float] = {}
    for engine, char in candidates.items():
        if char is None:
            continue
        weight = engine_weights.get(engine, 1.0) * confidences.get(engine, 0.5)
        votes[char] = votes.get(char, 0.0) + weight

    if not votes:
        return "", 0.0

    voted_char = max(votes, key=votes.get)
    return voted_char, votes[voted_char]


def vote_aligned_text(
    aligned_positions: list[AlignedPosition],
    confidences: dict[str, float],
    engine_weights: dict[str, float] | None = None,
) -> tuple[str, float]:
    """Vote across all aligned positions to produce final text.

    Args:
        aligned_positions: List of AlignedPosition objects.
        confidences: Dict of engine -> confidence.
        engine_weights: Weight for each engine.

    Returns:
        Tuple of (voted_text, average_confidence).
    """
    if not aligned_positions:
        return "", 0.0

    chars: list[str] = []
    total_weight = 0.0

    for pos in aligned_positions:
        voted_char, weight = weighted_vote_character(
            pos.candidates,
            confidences,
            engine_weights,
        )
        chars.append(voted_char)
        total_weight += weight

    voted_text = "".join(chars)
    avg_confidence = total_weight / len(aligned_positions) if aligned_positions else 0.0

    return voted_text, avg_confidence
