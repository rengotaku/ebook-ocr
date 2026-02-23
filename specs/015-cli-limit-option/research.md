# Research: CLIコマンドへの--limitオプション追加

**Date**: 2026-02-22
**Branch**: 015-cli-limit-option

## Research Tasks

### 1. 既存CLIの実装パターン

**調査結果**: 4つのCLIファイルを分析

| CLI | 基盤関数 | ファイル取得パターン |
|-----|----------|---------------------|
| deduplicate.py | `deduplicate_frames()` | `sorted(src.glob("frame_*.png"))` |
| detect_layout.py | `detect_layout()` | `sorted(pages_path.glob("*.png"))` |
| run_ocr.py | `run_rover_batch()` | `sorted(pages_path.glob("*.png"))` |
| consolidate.py | `consolidate_rover_output()` | `sorted(rover_dir.glob("*.txt"))` |

**結論**: 全CLIが同じパターン（sorted glob → 処理）を使用。リストスライスで容易に制限可能。

### 2. argparseベストプラクティス

**調査結果**:
- `type=int` で整数バリデーション自動化
- `help` でドキュメント化
- `default=None` で後方互換性維持

**採用パターン**:
```python
parser.add_argument(
    "--limit",
    type=int,
    help="Process only first N files (for testing)",
)
```

### 3. Makefile変数展開

**調査結果**: 既存Makefileで `$(if ...)` 構文を使用可能

```makefile
$(eval LIMIT_OPT := $(if $(LIMIT),--limit $(LIMIT),))
```

**結論**: 条件付きオプション展開はMakefileの標準パターン。

### 4. テスト戦略

**調査結果**:
- 既存テストは `tests/` ディレクトリに配置
- pytest使用、フィクスチャ活用
- CLI単体テストとE2Eテストの分離

**採用アプローチ**:
1. 各CLIに対してユニットテスト作成（モック使用）
2. 統合テストはMakefile経由で手動実行

## Decisions Summary

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| CLIと基盤関数両方に`limit`追加 | 関心の分離、テスト容易性 | CLIのみ変更（基盤関数がテスト困難） |
| `limit=None`デフォルト | 後方互換性維持 | 必須パラメータ化（既存コード破壊） |
| 標準エラー出力に制限情報表示 | ユーザーフィードバック | サイレント処理（デバッグ困難） |
| `test-run`ターゲット名 | ユーザー要望 | `quick-test`（Issue#19の提案） |

## Open Questions

なし - 全ての技術的詳細が確定。
