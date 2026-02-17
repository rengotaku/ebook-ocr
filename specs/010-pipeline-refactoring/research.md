# Research: パイプライン・リファクタリング

**Date**: 2026-02-17
**Feature**: 010-pipeline-refactoring

## 1. CLI構造のベストプラクティス

### Decision: サブコマンドパターンを採用しない

**Rationale**: 各ステップは完全に独立したスクリプトとして実行される。`python -m src.cli.extract_frames`のような直接実行が最もシンプル。

**Alternatives considered**:
- Click + サブコマンド: 過剰な抽象化、依存追加不要
- Typer: 同上
- 単一エントリーポイント: 現在のpipeline.pyと同じ問題

### 各CLIスクリプトの共通パターン

```python
"""Script description."""
import argparse
import sys
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("input", help="Input path")
    parser.add_argument("-o", "--output", required=True, help="Output path")
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        return 1

    # 処理実行
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## 2. 命名規則統一

### Decision: 「rover」に統一

**Rationale**: Issue#12で明示的に指定されている。

**Migration strategy**:
1. 新しいモジュール名でファイル作成
2. 既存のインポートを更新
3. 旧ファイルを削除

**Naming conventions**:
- モジュール: `rover/` (パッケージ)
- 関数: `run_rover_*`ではなく`ensemble_*`, `align_*`など機能名
- 変数: `yomitoku_device` → `device`

## 3. フォルダ構造

### Decision: 機能別パッケージ構造

**Rationale**:
- 各パッケージは単一責務
- テストの並列化が容易
- 依存関係が明確

**Package layout**:
```
src/
├── cli/          # CLIエントリーポイント（薄いラッパー）
├── rover/        # OCRアンサンブル
├── preprocessing/# 前処理
├── layout/       # レイアウト解析
└── book_converter/ # 既存（変更なし）
```

## 4. 後方互換性コード除去

### Decision: 3カテゴリに分類して対処

**Category A: 除去対象（後方互換性）**
- `book_converter/parser.py:584` - "Legacy patterns below for backward compatibility"

**Category B: 維持（エラーリカバリ）**
- LLM失敗時のルールベースフォールバック
- OCRエンジン失敗時の次エンジン試行

**Category C: リファクタリング（名称のみ）**
- `ENGINE_PRIORITY["FALLBACK"]` → `ENGINE_PRIORITY["DEFAULT"]`

## 5. テスト戦略

### Decision: 既存テストを維持しつつ新構造に適応

**Strategy**:
1. リファクタリング前に全テストがパスすることを確認
2. モジュール移動時にimportパスを更新
3. 新CLIスクリプトには統合テストを追加
4. 分割ファイルにはユニットテストを追加

## 6. 移行順序

### Decision: 依存関係の逆順

**Order**:
1. `utils.py` (依存なし) - 移動のみ
2. `preprocessing/` - 基盤モジュール
3. `layout/` - preprocessingに依存
4. `rover/` - layout, preprocessingに依存
5. `cli/` - 全モジュールに依存
6. 旧ファイル削除

## Summary

| Topic | Decision | Key Reason |
|-------|----------|------------|
| CLI構造 | 独立スクリプト | シンプル、直接実行可能 |
| 命名規則 | rover統一 | Issue#12の要求 |
| フォルダ構造 | 機能別パッケージ | 単一責務、テスト容易 |
| 後方互換コード | カテゴリ別対処 | エラーリカバリは維持 |

## Out of Scope

以下は別Issue（011-lint-file-split）で対応:
- ruff導入とpre-commit hook設定
- 600行超ファイルの分割
