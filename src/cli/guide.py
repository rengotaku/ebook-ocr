"""Interactive setup guide for ebook-ocr pipeline.

Asks questions to determine the user's workflow and outputs
the recommended make commands to execute.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path


def _ask(question: str, default: str = "") -> str:
    """Ask a question and return the answer."""
    if default:
        prompt = f"{question} [{default}]: "
    else:
        prompt = f"{question}: "
    answer = input(prompt).strip()
    return answer if answer else default


def _ask_yn(question: str, default: bool = False) -> bool:
    """Ask a yes/no question."""
    suffix = "[Y/n]" if default else "[y/N]"
    answer = input(f"{question} {suffix}: ").strip().lower()
    if not answer:
        return default
    return answer in ("y", "yes")


def _find_video_candidates() -> list[str]:
    """Find video files in common locations."""
    extensions = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
    candidates = []
    for search_dir in [Path("movies"), Path("input"), Path(".")]:
        if search_dir.exists():
            for f in sorted(search_dir.iterdir()):
                if f.suffix.lower() in extensions and f.is_file():
                    candidates.append(str(f))
    return candidates[:10]


def _compute_hash(video_path: str) -> str | None:
    """Compute hash for video file."""
    try:
        from src.preprocessing.hash import compute_video_hash

        return compute_video_hash(video_path)
    except Exception:  # noqa: BLE001
        return None


@dataclass(frozen=True)
class GuideAnswers:
    """User answers from the interactive guide."""

    video_path: str
    is_spread: bool
    needs_trim: bool
    wants_preview: bool
    limit_val: str
    hashdir: str


def _ask_questions() -> GuideAnswers:
    """Ask all guide questions and return answers."""
    # Q1: Video file
    candidates = _find_video_candidates()
    if candidates:
        print("検出された動画ファイル:")
        for i, c in enumerate(candidates, 1):
            print(f"  {i}. {c}")
        print()

    video_path = _ask("Q1. 動画ファイルのパスは？")
    if not video_path:
        print("動画ファイルが指定されていません。終了します。", file=sys.stderr)
        sys.exit(1)

    if video_path.isdigit() and candidates:
        idx = int(video_path) - 1
        if 0 <= idx < len(candidates):
            video_path = candidates[idx]

    if not Path(video_path).exists():
        print(f"警告: {video_path} が見つかりません。パスを確認してください。", file=sys.stderr)

    is_spread = _ask_yn("Q2. 見開き（2ページが1画像）ですか？")
    needs_trim = _ask_yn("Q3. トリムは必要ですか？（余白・ヘッダー・フッター除去）")

    wants_preview = False
    if needs_trim:
        wants_preview = _ask_yn("Q4. トリム値を決めるためにプレビューしますか？", default=True)

    limit_val = ""
    if _ask_yn("Q5. テスト用に処理ページ数を制限しますか？"):
        limit_val = _ask("  何ページまで？", default="25")

    # Compute hash
    print()
    print("ハッシュ値を計算中...")
    video_hash = _compute_hash(video_path)
    if video_hash:
        hashdir = f"output/{video_hash}"
        print(f"出力ディレクトリ: {hashdir}")
    else:
        hashdir = "output/<hash>"
        print("ハッシュ計算をスキップしました（実行時に自動決定されます）")

    return GuideAnswers(
        video_path=video_path,
        is_spread=is_spread,
        needs_trim=needs_trim,
        wants_preview=wants_preview,
        limit_val=limit_val,
        hashdir=hashdir,
    )


def _print_preview_steps(answers: GuideAnswers, step: int) -> int:
    """Print preview-related steps. Returns next step number."""
    print(f"Step {step}. プレビューフレーム抽出:")
    print(f"   make preview-extract VIDEO={answers.video_path}")
    print()
    step += 1

    print(f"Step {step}. トリムグリッド生成（ガイド線で値を確認）:")
    print(f"   make preview-trim-grid HASHDIR={answers.hashdir}")
    print()
    step += 1

    print(f"Step {step}. グリッド画像を確認してトリム値を決定:")
    print(f"   open {answers.hashdir}/preview/trim-grid/")
    print("   赤=Top, 青=Bottom, 緑=Left, 橙=Right")
    print("   例: 赤3本目 = T:0.15 → GLOBAL_TRIM_TOP=0.15")
    print()
    return step + 1


def _print_run_step(answers: GuideAnswers, step: int) -> int:
    """Print the pipeline run step. Returns next step number."""
    print(f"Step {step}. フルパイプライン実行:")
    parts = [f"make run VIDEO={answers.video_path}"]
    if answers.is_spread:
        parts.append("SPREAD_MODE=spread")
    if answers.limit_val:
        parts.append(f"LIMIT={answers.limit_val}")
    if answers.needs_trim:
        parts.append("\\")
        print(f"   {' '.join(parts)}")
        print("     GLOBAL_TRIM_TOP=<値> GLOBAL_TRIM_BOTTOM=<値> \\")
        if answers.is_spread:
            print("     SPREAD_LEFT_PAGE_OUTER=<値> SPREAD_RIGHT_PAGE_OUTER=<値>")
        else:
            print("     GLOBAL_TRIM_LEFT=<値> GLOBAL_TRIM_RIGHT=<値>")
    else:
        print(f"   {' '.join(parts)}")
    print()
    return step + 1


def main() -> None:
    """Run the interactive guide."""
    print()
    print("=" * 50)
    print("  ebook-ocr セットアップガイド")
    print("=" * 50)
    print()

    answers = _ask_questions()

    print()
    print("=" * 50)
    print("  実行手順")
    print("=" * 50)
    print()

    step = 1

    if answers.wants_preview:
        step = _print_preview_steps(answers, step)

    step = _print_run_step(answers, step)

    print(f"Step {step}. 結果確認:")
    print(f"   open {answers.hashdir}/book.xml")
    print()


if __name__ == "__main__":
    main()
