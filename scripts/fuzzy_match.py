#!/usr/bin/env python3
import sys
import unicodedata
import re
from difflib import SequenceMatcher
from pathlib import Path

def normalize(text):
    """全角半角・スペース・改行を正規化"""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r'\s+', '', text)
    return text.lower()

def fuzzy_match(query, text, threshold=0.8):
    """編集距離ベースの曖昧マッチング"""
    norm_query = normalize(query)
    norm_text = normalize(text)

    if not norm_query or not norm_text:
        return 0.0

    # 部分文字列での最大類似度
    max_ratio = 0
    query_len = len(norm_query)

    for i in range(len(norm_text) - query_len + 1):
        substr = norm_text[i:i+query_len]
        ratio = SequenceMatcher(None, norm_query, substr).ratio()
        max_ratio = max(max_ratio, ratio)

    # クエリより短いテキストの場合も考慮
    if len(norm_text) < query_len:
        ratio = SequenceMatcher(None, norm_query, norm_text).ratio()
        max_ratio = max(max_ratio, ratio)

    return max_ratio

def search_file(filepath, query, threshold=0.8, context_lines=0, start_line=1, max_join_lines=10):
    """ファイルから曖昧マッチする行を検索（複数行結合対応）"""
    lines = Path(filepath).read_text(encoding='utf-8').splitlines()
    matches = []
    query_len = len(normalize(query))

    for i, line in enumerate(lines):
        if i + 1 < start_line:
            continue

        # 複数行を結合してマッチを試みる
        best_match = None
        combined_text = ""
        combined_lines = []

        for j in range(max_join_lines):
            if i + j >= len(lines):
                break

            combined_lines.append(lines[i + j])
            combined_text = " ".join(combined_lines)
            combined_norm_len = len(normalize(combined_text))

            # マッチ判定
            ratio = fuzzy_match(query, combined_text, threshold)
            if ratio >= threshold:
                if best_match is None or ratio > best_match['ratio']:
                    best_match = {
                        'line_num': i + 1,
                        'line_end': i + j + 1,
                        'line': combined_text,
                        'lines_joined': j + 1,
                        'ratio': ratio,
                    }

            # クエリ文字数以上になったら終了
            if combined_norm_len >= query_len:
                break

        if best_match:
            # コンテキスト行を含める
            start = max(0, i - context_lines)
            end = min(len(lines), best_match['line_end'] + context_lines)
            context = lines[start:end]

            best_match['context'] = context
            best_match['context_start'] = start + 1
            matches.append(best_match)

    # 重複除去（同じ行範囲を含むマッチを除外）
    matches = _deduplicate_matches(matches)

    return sorted(matches, key=lambda x: x['ratio'], reverse=True)

def _deduplicate_matches(matches):
    """重複するマッチを除去（より高いratioを優先）"""
    if not matches:
        return matches

    # ratioでソート（高い順）
    sorted_matches = sorted(matches, key=lambda x: x['ratio'], reverse=True)
    result = []
    covered_lines = set()

    for match in sorted_matches:
        match_lines = set(range(match['line_num'], match['line_end'] + 1))
        # 既にカバーされている行と重複がなければ追加
        if not match_lines & covered_lines:
            result.append(match)
            covered_lines.update(match_lines)

    return result

def print_matches(matches, show_context=False):
    """マッチ結果を表示"""
    if not matches:
        print("No matches found.")
        return

    for match in matches:
        similarity = int(match['ratio'] * 100)
        lines_info = ""
        if match.get('lines_joined', 1) > 1:
            lines_info = f" ({match['lines_joined']}行結合: {match['line_num']}-{match['line_end']})"

        # 結合された行を | で表示
        display_line = match['line'].replace('  ', ' ')
        if match.get('lines_joined', 1) > 1:
            display_line = " | ".join(match['line'].split('  '))

        print(f"\n{match['line_num']:4d} [{similarity}%]: {display_line}{lines_info}")

        if show_context and len(match.get('context', [])) > 1:
            print("  Context:")
            for idx, ctx_line in enumerate(match['context']):
                line_num = match['context_start'] + idx
                if match['line_num'] <= line_num <= match.get('line_end', match['line_num']):
                    marker = ">>>"
                else:
                    marker = "   "
                print(f"    {marker} {line_num:4d}: {ctx_line}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fuzzy text matcher with normalization')
    parser.add_argument('query', help='Search query')
    parser.add_argument('file', help='File to search')
    parser.add_argument('-t', '--threshold', type=float, default=0.8,
                       help='Similarity threshold (0.0-1.0, default: 0.8)')
    parser.add_argument('-c', '--context', type=int, default=0,
                       help='Number of context lines to show')
    parser.add_argument('-n', '--max-results', type=int, default=None,
                       help='Maximum number of results to show')
    parser.add_argument('-s', '--start-line', type=int, default=1,
                       help='Start searching from this line number (default: 1)')
    parser.add_argument('-j', '--max-join-lines', type=int, default=10,
                       help='Maximum lines to join for matching (default: 10)')

    args = parser.parse_args()

    matches = search_file(
        args.file, args.query, args.threshold, args.context,
        args.start_line, args.max_join_lines
    )

    if args.max_results:
        matches = matches[:args.max_results]

    print(f"Query: {args.query}")
    print(f"Normalized: {normalize(args.query)}")
    print(f"Threshold: {args.threshold}")
    print(f"Found {len(matches)} matches")

    print_matches(matches, show_context=args.context > 0)
