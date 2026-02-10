#!/usr/bin/env python3
"""TOCエントリごとにbook.mdから最もマッチする行を検索"""
import sys
import re
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

# fuzzy_match.pyをインポート
sys.path.insert(0, str(Path(__file__).parent))
from fuzzy_match import search_file, normalize, fuzzy_match

def extract_key_phrases(toc_entry: str) -> list[str]:
    """TOCエントリからキーフレーズを抽出

    Args:
        toc_entry: TOCエントリ（例: "Episode 07 実装できない「ふんわり仕様」"）

    Returns:
        正規化されたキーフレーズリスト（例: ["episode07", "ふんわり仕様"]）
    """
    phrases = []

    # Episode XX または Chapter X を抽出
    if m := re.search(r'(Episode|Chapter)\s+\d+', toc_entry):
        phrases.append(normalize(m.group()))

    # 「...」（鍵括弧内）を抽出
    for m in re.finditer(r'「([^」]+)」', toc_entry):
        phrases.append(normalize(m.group(1)))

    # Column の場合は後続テキストも追加
    if toc_entry.startswith('Column'):
        # Columnの後のテキスト
        text = re.sub(r'^Column\s+', '', toc_entry)
        text = re.sub(r'「[^」]+」', '', text).strip()
        if text:
            phrases.append(normalize(text))

    return phrases

def search_by_key_phrases(entry: str, content_file: str, threshold: float, start_line: int, max_range: int = 30) -> dict | None:
    """キーフレーズ分割マッチ（fallback用）

    Args:
        entry: TOCエントリ
        content_file: 検索対象ファイル
        threshold: マッチ閾値
        start_line: 検索開始行
        max_range: キーフレーズ間の最大行数

    Returns:
        マッチ結果 or None
    """
    lines = Path(content_file).read_text(encoding='utf-8').splitlines()
    key_phrases = extract_key_phrases(entry)

    if not key_phrases:
        return None

    # 各phraseの出現位置を検索
    positions = []
    matched_lines = []

    for phrase in key_phrases:
        best_pos = None
        best_ratio = 0

        for i in range(start_line - 1, len(lines)):
            # 10行結合してマッチ
            end_idx = min(i + 10, len(lines))
            combined = " ".join(lines[i:end_idx])
            ratio = fuzzy_match(phrase, combined, threshold)

            if ratio >= threshold and ratio > best_ratio:
                best_pos = i + 1  # 1-indexed
                best_ratio = ratio
                matched_lines.append((i + 1, phrase, ratio))

        if best_pos:
            positions.append(best_pos)
        else:
            # 1つでもマッチしなければ失敗
            return None

    # すべてのphraseが範囲内に存在するか
    if len(positions) == len(key_phrases):
        if max(positions) - min(positions) <= max_range:
            start = min(positions)
            end = max(positions)

            # 平均一致率を計算
            avg_ratio = sum(r for _, _, r in matched_lines) / len(matched_lines)

            return {
                'toc': entry,
                'line_num': start,
                'line_end': end,
                'ratio': avg_ratio,
                'matched': f"[Key-phrase match: {len(key_phrases)} phrases in {end-start+1} lines]",
                'lines_joined': end - start + 1,
                'method': 'key_phrase',
            }

    return None

def _search_single_entry(args):
    """単一エントリを検索（並列処理用）"""
    entry, content_file, threshold, start_line = args

    # 通常の全文マッチを試みる
    matches = search_file(content_file, entry, threshold=threshold, max_join_lines=10, start_line=start_line)

    if matches:
        best = matches[0]
        return {
            'toc': entry,
            'line_num': best['line_num'],
            'line_end': best.get('line_end', best['line_num']),
            'ratio': best['ratio'],
            'matched': best['line'],
            'lines_joined': best.get('lines_joined', 1),
            'method': 'full_text',
        }

    # Fallback: キーフレーズ分割マッチ
    key_phrase_result = search_by_key_phrases(entry, content_file, threshold=0.7, start_line=start_line)
    if key_phrase_result:
        return key_phrase_result

    # どちらも失敗
    return {
        'toc': entry,
        'line_num': None,
        'line_end': None,
        'ratio': 0.0,
        'matched': '--- NOT FOUND ---',
        'lines_joined': 0,
        'method': 'none',
    }

def find_toc_end(content_file: str) -> int:
    """TOCセクション終了行を検出"""
    lines = Path(content_file).read_text(encoding='utf-8').splitlines()
    last_toc_end = 0
    for i, line in enumerate(lines):
        if '<!-- /toc -->' in line:
            last_toc_end = i + 1
    return last_toc_end + 1  # 次の行から開始

def match_toc_entries(toc_file: str, content_file: str, threshold: float = 0.6, workers: int = 4, start_line: int = None):
    """各TOCエントリに対して最もマッチする行を検索（並列処理）"""
    toc_lines = Path(toc_file).read_text(encoding='utf-8').splitlines()

    # 有効なエントリを抽出
    entries = []
    for toc_entry in toc_lines:
        entry = toc_entry.strip()
        if entry and not entry.startswith('<!--'):
            entries.append(entry)

    # TOC終了位置を自動検出
    if start_line is None:
        start_line = find_toc_end(content_file)
        print(f"# TOC終了検出: {start_line}行目から検索開始", file=sys.stderr)

    # 並列処理
    results = []
    args_list = [(entry, content_file, threshold, start_line) for entry in entries]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_search_single_entry, args): args[0] for args in args_list}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # 元の順序でソート
    entry_order = {e: i for i, e in enumerate(entries)}
    results.sort(key=lambda x: entry_order.get(x['toc'], 999))

    return results

def print_results(results, show_all=False):
    """結果を表示"""
    print(f"{'TOCエントリ':<50} {'行番号':>8} {'一致率':>8} {'結合':>4} {'方法':>8}")
    print("-" * 90)

    for r in results:
        ratio_pct = int(r['ratio'] * 100)
        line_info = f"{r['line_num']}" if r['line_num'] else "N/A"
        if r.get('line_end') and r['line_end'] != r['line_num']:
            line_info = f"{r['line_num']}-{r['line_end']}"

        toc_display = r['toc'][:48] + '..' if len(r['toc']) > 50 else r['toc']

        # 色分け
        if ratio_pct >= 80:
            status = "✓"
        elif ratio_pct >= 70:
            status = "△"
        else:
            status = "✗"

        # マッチ方法
        method = r.get('method', 'unknown')
        method_display = 'Full' if method == 'full_text' else 'Key' if method == 'key_phrase' else '-'

        print(f"{status} {toc_display:<48} {line_info:>8} {ratio_pct:>7}% {r['lines_joined']:>4} {method_display:>8}")

        if show_all and r['matched'] != '--- NOT FOUND ---':
            matched_short = r['matched'][:70] + '...' if len(r['matched']) > 70 else r['matched']
            print(f"  → {matched_short}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Match TOC entries to content file')
    parser.add_argument('toc', help='TOC file')
    parser.add_argument('content', help='Content file to search')
    parser.add_argument('-t', '--threshold', type=float, default=0.6,
                       help='Similarity threshold (default: 0.6)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Show matched text')
    parser.add_argument('--json', action='store_true',
                       help='Output as JSON')
    parser.add_argument('-s', '--start-line', type=int, default=None,
                       help='Start searching from this line (default: auto-detect after TOC)')
    parser.add_argument('-w', '--workers', type=int, default=4,
                       help='Number of parallel workers (default: 4)')

    args = parser.parse_args()

    results = match_toc_entries(args.toc, args.content, args.threshold, workers=args.workers, start_line=args.start_line)

    if args.json:
        import json
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print_results(results, show_all=args.verbose)

        # サマリー
        found = sum(1 for r in results if r['line_num'])
        total = len(results)
        high_match = sum(1 for r in results if r['ratio'] >= 0.8)
        full_text = sum(1 for r in results if r.get('method') == 'full_text')
        key_phrase = sum(1 for r in results if r.get('method') == 'key_phrase')
        print()
        print(f"合計: {total}件, 検出: {found}件, 高一致(≥80%): {high_match}件")
        print(f"方法: 全文={full_text}件, キーフレーズ={key_phrase}件")
