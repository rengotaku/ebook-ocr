"""LLM-based TOC entry classifier.

This module provides LLM-based classification for TOC entries
to improve accuracy in distinguishing chapter/section/subsection levels.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from src.book_converter.models import TocEntry as ModelTocEntry

# Optional requests import for Ollama API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


@dataclass(frozen=True)
class TocEntry:
    """TOC entry with classification."""

    text: str
    level: str  # "chapter", "section", "subsection", "other"
    number: str
    page: str = ""


def _convert_level_to_int(level_str: str) -> int:
    """Convert level string to integer.

    Args:
        level_str: Level string ("chapter", "section", "subsection", "other")

    Returns:
        Integer level (1-5). "other" defaults to 1.

    Example:
        >>> _convert_level_to_int("chapter")
        1
        >>> _convert_level_to_int("section")
        2
        >>> _convert_level_to_int("subsection")
        3
    """
    level_map = {
        "chapter": 1,
        "section": 2,
        "subsection": 3,
        "other": 1,  # Default to level 1
    }
    return level_map.get(level_str.lower(), 1)


# System prompt for batch TOC classification
BATCH_SYSTEM_PROMPT = """You are a TOC (Table of Contents) parser and classifier.

Parse the complete TOC text into individual entries with proper classification.

Classification rules:
- "chapter": Top-level with single number or "Chapter N" (e.g., "1", "Chapter 1", "第1章")
- "section": Two-part number (e.g., "2.1", "3.2")
- "subsection": Three+ part number (e.g., "2.1.1", "2.1.1.1")
- "other": No hierarchical number (Episode, Column, etc.)

CRITICAL NUMBER PARSING:
- "2.1.1 Title" → number="2.1.1" (subsection)
- "2.1 Title" → number="2.1" (section)
- "Chapter 1 Title" → number="1" (chapter)
- "Episode 01 Title" → number="" (other)

Return ONLY a JSON array:
[
  {"level": "chapter", "number": "1", "title": "SREとは"},
  {"level": "section", "number": "2.1", "title": "SLOを理解するための4つの要素"},
  {"level": "subsection", "number": "2.1.1", "title": "SLA"},
  {"level": "other", "number": "", "title": "Episode 01 Getting Started"}
]

IMPORTANT:
- Preserve original number formats exactly (e.g., "2.1.1" not "1.1")
- Extract titles without number prefixes
- Return only JSON, no explanations
"""


def classify_toc_batch_with_llm(toc_text: str, model: str = "gpt-oss:20b", preserve_newlines: bool = False) -> list[ModelTocEntry]:
    """Classify entire TOC text using LLM (batch processing).

    Args:
        toc_text: Complete TOC text (normalized or raw)
        model: Ollama model name to use
        preserve_newlines: If True, use raw text with newlines preserved

    Returns:
        List of TocEntry objects (from models module with int level)

    Example:
        >>> toc = "Chapter 1 SREとは\\n2.1 SLOを理解するための4つの要素\\n2.1.1 SLA"
        >>> classify_toc_batch_with_llm(toc, preserve_newlines=True)
        [TocEntry(text="SREとは", level=1, number="1", page=""), ...]
    """
    if not REQUESTS_AVAILABLE:
        return []

    if not toc_text.strip():
        return []

    try:
        # Call Ollama API with batch prompt (without JSON format to allow arrays)
        messages = [
            {"role": "system", "content": BATCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Parse this TOC:\n\n{toc_text}"}
        ]

        response = _call_ollama_api(model, messages, use_json_format=False)

        if not response:
            return []

        # Extract JSON array from response (may have surrounding text)
        import re
        json_match = re.search(r'\[[\s\S]*\]', response)
        if not json_match:
            return []

        json_str = json_match.group(0)
        entries_data = json.loads(json_str)

        if not isinstance(entries_data, list):
            return []

        # Convert to TocEntry objects with int level
        results = []
        for entry_dict in entries_data:
            if not isinstance(entry_dict, dict):
                continue

            level_str = entry_dict.get("level", "other")
            results.append(ModelTocEntry(
                text=entry_dict.get("title", ""),
                level=_convert_level_to_int(level_str),
                number=entry_dict.get("number", ""),
                page=""
            ))

        return results

    except (json.JSONDecodeError, KeyError, Exception):
        # Fallback to empty list if LLM fails
        return []


def classify_toc_entry_with_llm(entry_text: str, model: str = "gpt-oss:20b") -> ModelTocEntry | None:
    """Classify TOC entry using LLM.

    Args:
        entry_text: Raw TOC entry text
        model: Ollama model name to use

    Returns:
        TocEntry (from models module with int level) or None if classification fails

    Example:
        >>> classify_toc_entry_with_llm("2.1 SLOを理解するための4つの要素")
        TocEntry(text="SLOを理解するための4つの要素", level=2, number="2.1", page="")
    """
    if not REQUESTS_AVAILABLE:
        return None

    if not entry_text.strip():
        return None

    try:
        # Call Ollama API
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this TOC entry: '{entry_text}'"}
        ]

        response = _call_ollama_api(model, messages)

        if not response:
            return None

        # Parse JSON response
        result = json.loads(response)

        level_str = result.get("level", "other")
        return ModelTocEntry(
            text=result.get("title", entry_text),
            level=_convert_level_to_int(level_str),
            number=result.get("number", ""),
            page=""
        )

    except (json.JSONDecodeError, KeyError, Exception):
        # Fallback to None if LLM fails
        return None


def _call_ollama_api(model: str, messages: list[dict], use_json_format: bool = False) -> str | None:
    """Call Ollama REST API.

    Args:
        model: Model name (e.g., "gpt-oss:20b")
        messages: Chat messages
        use_json_format: If True, use Ollama's JSON format mode (for single objects)

    Returns:
        JSON string response or None on failure
    """
    if not REQUESTS_AVAILABLE:
        return None

    try:
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.0,  # Deterministic output
                "top_p": 1.0,
            }
        }

        # Only use format: json for single object responses
        if use_json_format:
            payload["format"] = "json"

        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        content = result.get("message", {}).get("content", "")
        return content.strip()

    except (requests.RequestException, json.JSONDecodeError, Exception):
        return None


def is_llm_classification_enabled() -> bool:
    """Check if LLM classification is enabled.

    Returns:
        True if LLM classification should be used

    Checks:
        1. REQUESTS_AVAILABLE (import succeeded)
        2. USE_LLM_TOC_CLASSIFIER environment variable
    """
    if not REQUESTS_AVAILABLE:
        return False

    env_var = os.environ.get("USE_LLM_TOC_CLASSIFIER", "false").lower()
    return env_var in ("true", "1", "yes")
