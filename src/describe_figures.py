"""Replace figure/table markers in OCR text with VLM-generated descriptions."""

from __future__ import annotations

import re
import time
from pathlib import Path

import requests
from PIL import Image

from src.utils import encode_image_file, encode_pil_image


FIGURE_MARKER_RE = re.compile(
    r"\[(FIGURE|TABLE): (figures/[^\s]+\.png)(?: \(confidence: [\d.]+\))?\]"
)

SYSTEM_PROMPT = """\
You are an expert at describing visual content in Japanese academic/technical books.
Given a cropped image of a figure, table, or chart, provide a concise Markdown description.
- For tables: reproduce the table in Markdown table format.
- For figures/charts: describe what is shown in 2-5 sentences.
- For formulas: write the formula in LaTeX notation.
Respond ONLY with the description, no preamble."""

USER_PROMPT = "この画像の内容を説明してください。"

VLM_DEFAULT_OPTIONS = {
    "temperature": 0.1,
    "num_predict": 2048,
    "repeat_penalty": 1.3,
    "repeat_last_n": -1,
}


def warm_up_vlm_model(
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 300,
) -> None:
    """Warm up the VLM model by sending a dummy request to load it into memory.

    Args:
        model: Ollama vision model name.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds (longer for initial load).

    Raises:
        requests.RequestException: If the warm-up request fails.
    """
    print(f"  Loading VLM model {model}...", end="", flush=True)
    start = time.time()

    # Create a minimal 1x1 white image
    dummy_img = Image.new("RGB", (1, 1), color="white")
    image_b64 = encode_pil_image(dummy_img)

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": "test", "images": [image_b64]},
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 1,
        },
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    elapsed = time.time() - start
    print(f" loaded in {elapsed:.1f}s")


def _describe_single(
    image_path: str,
    fig_type: str,
    model: str,
    base_url: str,
    timeout: int,
    options: dict | None = None,
) -> str:
    """Send a cropped figure image to VLM and get a description."""
    image_b64 = encode_image_file(image_path)
    merged_options = {**VLM_DEFAULT_OPTIONS, **(options or {})}

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT, "images": [image_b64]},
        ],
        "stream": False,
        "options": merged_options,
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result = response.json()
    return result["message"]["content"].strip()


def describe_figures(
    text_file: str,
    output_file: str,
    figures_dir: str,
    layout: dict | None = None,
    model: str = "gemma3:12b",
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
    min_confidence: float = 0.7,
    options: dict | None = None,
) -> str:
    """Replace figure markers in OCR text with VLM descriptions.

    Args:
        text_file: Path to Tesseract OCR output (book.txt).
        output_file: Path to write final Markdown (book.md).
        figures_dir: Directory containing cropped figure images.
        layout: Layout dict (unused, kept for pipeline interface).
        model: Ollama vision model name.
        base_url: Ollama API base URL.
        timeout: Per-figure VLM timeout in seconds.
        min_confidence: Minimum confidence (markers below this are removed).
        options: Ollama generation options (temperature, repeat_penalty, etc.).

    Returns:
        Path to the output file.
    """
    text_path = Path(text_file)
    if not text_path.exists():
        print(f"Error: OCR text file not found: {text_file}")
        return output_file

    text = text_path.read_text(encoding="utf-8")
    out_dir = text_path.parent
    fig_base = out_dir  # figures/ paths are relative to output dir

    markers = list(FIGURE_MARKER_RE.finditer(text))
    if not markers:
        print("No figure markers found in OCR text. Copying as-is.")
        Path(output_file).write_text(text, encoding="utf-8")
        return output_file

    print(f"Found {len(markers)} figure markers to describe with VLM ({model})")

    # Warm up VLM model to avoid timeout on first figure
    try:
        warm_up_vlm_model(model, base_url, timeout=300)
    except requests.RequestException as e:
        print(f"  VLM warm-up failed: {e}")
        print("  Continuing anyway (first figure may timeout)...")

    replacements: list[tuple[str, str]] = []
    described = 0
    total_start = time.time()

    for i, match in enumerate(markers, 1):
        fig_type = match.group(1)
        rel_path = match.group(2)
        full_path = fig_base / rel_path
        marker_text = match.group(0)

        if not full_path.exists():
            print(f"  [{i}/{len(markers)}] {rel_path} -> MISSING, removing marker")
            replacements.append((marker_text, ""))
            continue

        print(f"  [{i}/{len(markers)}] {rel_path} ({fig_type})", end="", flush=True)
        start = time.time()

        try:
            description = _describe_single(
                str(full_path), fig_type, model, base_url, timeout,
                options=options,
            )
            elapsed = time.time() - start
            print(f" -> {len(description)} chars ({elapsed:.1f}s)")

            md_block = f"\n<!-- {fig_type}: {rel_path} -->\n{description}\n"
            replacements.append((marker_text, md_block))
            described += 1
        except requests.RequestException as e:
            elapsed = time.time() - start
            print(f" -> ERROR ({elapsed:.1f}s): {e}")
            replacements.append((marker_text, f"\n[{fig_type} DESCRIPTION ERROR: {e}]\n"))

    result_text = text
    for old, new in replacements:
        result_text = result_text.replace(old, new, 1)

    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    Path(output_file).write_text(result_text, encoding="utf-8")

    total_elapsed = time.time() - total_start
    print(f"\nFigure description complete in {total_elapsed:.1f}s")
    print(f"  Described: {described}/{len(markers)} figures")
    print(f"  Output: {output_file}")
    return output_file
