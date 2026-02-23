# Phase 3: Implementation (GREEN) + Verification 完了レポート

**日時**: 2026-02-23
**フェーズ**: Phase 3 - User Story 2 (個別CLIコマンドでの画像数制限)
**ステータス**: ✅ 完了 (GREEN)

## 概要

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 3 (US2) |
| 完了タスク数 | 6/6 |
| 変更ファイル数 | 2 (テストファイルのみ) |
| 全テスト結果 | 1329 passed, 6 skipped |
| リグレッション | なし |

## 実行したタスク

| タスクID | 説明 | ステータス |
|---------|------|----------|
| T032 | REDテストを読み込み | ✅ 完了 |
| T033 | エッジケース対応を確認・調整 | ✅ 完了 (テスト修正のみ) |
| T034 | `make test` PASS確認 (GREEN) | ✅ 完了 |
| T035 | リグレッションなし確認 | ✅ 完了 |
| T036 | フェーズ出力を生成 | ✅ 完了 |

## 変更ファイル一覧

### テストデータ生成関数の修正

Phase 3では、実装コードの変更は不要でした。RED testで検出された失敗は、テストデータの問題によるものでした。

#### 1. tests/cli/test_limit_backward_compat.py

**問題**:
- 1x1ピクセルPNGは知覚ハッシュ (perceptual hash) により重複と判定される
- `detect_layout`は単一の`layout.json`ファイルを出力するが、テストはページ別JSONファイルを期待していた

**修正内容**:
- `_write_distinct_png()`: 1x1 PNG → 16x16 PNGに変更し、ユニークなパターンを生成
- `test_detect_layout_without_limit_processes_all()`: layout.json内のページ数をカウントするように修正

#### 2. tests/cli/test_limit_edge_cases.py

**同様の修正**:
- `_write_distinct_png()`: 1x1 PNG → 16x16 PNGに変更
- `test_detect_layout_limit_greater_than_file_count()`: layout.json内のページ数をカウント

### 修正内容の詳細

#### PNG生成関数の改善

```python
# Before (1x1 PNG with minimal color variation)
def _write_distinct_png(path: Path, *, color_r: int = 255) -> None:
    # 1x1 PNG with single pixel color variation
    # → Perceptual hash detected these as duplicates

# After (16x16 PNG with unique patterns)
def _write_distinct_png(path: Path, *, color_r: int = 255) -> None:
    """Write a distinct PNG file that won't be detected as duplicate by perceptual hash."""
    from PIL import Image

    # Create a 16x16 image with a unique pattern based on color_r
    img = Image.new("RGB", (16, 16))
    pixels = img.load()

    # Create a unique pattern for each image
    for y in range(16):
        for x in range(16):
            # Different patterns based on color_r to ensure hash differences
            if (x + y + color_r // 50) % 3 == 0:
                pixels[x, y] = (color_r & 0xFF, 0, 0)
            elif (x + y + color_r // 50) % 3 == 1:
                pixels[x, y] = (0, color_r & 0xFF, 0)
            else:
                pixels[x, y] = (0, 0, color_r & 0xFF)

    img.save(path)
```

#### detect_layout テストのアサーション修正

```python
# Before (期待: ページ別JSONファイル)
output_files = sorted(output_dir.glob("*.json"))
assert len(output_files) == 5, f"Expected 5 layout results..."

# After (実際の出力形式: 単一のlayout.json)
import json

layout_json = output_dir / "layout.json"
assert layout_json.exists(), "layout.json should be created"

with open(layout_json) as f:
    layout_data = json.load(f)
assert len(layout_data) == 5, f"Expected 5 pages in layout.json..."
```

## テスト結果

### 全テスト実行結果

```
1329 passed, 6 skipped in 119.24s (0:01:59)
```

- **新規FAILテスト**: 0件 (全てGREEN)
- **既存テストのリグレッション**: なし
- **ruff check**: All checks passed
- **ruff format**: 2 files left unchanged

### GREEN確認済みテスト

Phase 3で追加されたテスト (全てPASS):

#### test_limit_backward_compat.py
- ✅ `test_deduplicate_without_limit_processes_all` - --limitなしで全5フレーム処理
- ✅ `test_detect_layout_without_limit_processes_all` - --limitなしで全5ページ処理
- ✅ `test_run_ocr_without_limit_processes_all` - --limitなしで全5ページ処理
- ✅ `test_consolidate_without_limit_processes_all` - --limitなしで全5ページ処理

#### test_limit_edge_cases.py
- ✅ `test_deduplicate_limit_greater_than_file_count` - --limit 100で全3ファイル処理
- ✅ `test_detect_layout_limit_greater_than_file_count` - --limit 100で全3ページ処理
- ✅ `test_run_ocr_limit_greater_than_file_count` - --limit 100で全3ページ処理
- ✅ `test_consolidate_limit_greater_than_file_count` - --limit 100で全3ページ処理
- ✅ `test_deduplicate_limit_one_file` - --limit 1で1ファイルのみ処理
- ✅ `test_consolidate_limit_one_file` - --limit 1で1ファイルのみ処理

## 実装結果の分析

### 実装変更不要の理由

Phase 2で実装された`--limit`機能は既に以下を正しく処理していた:

1. **後方互換性**: `--limit`なしで全ファイルを処理 (デフォルト動作)
2. **エッジケース**: `--limit > ファイル数`でエラーなく全ファイルを処理
3. **最小単位**: `--limit 1`で正確に1ファイルのみ処理

REDテストの失敗は**テストデータの品質問題**によるもので、実装には問題がなかった。

### 根本原因

1. **deduplicate系テスト**:
   - 1x1 PNGは知覚ハッシュアルゴリズムにとって区別が困難
   - わずかな色の違い (RGB値の差) ではハッシュ距離が閾値以下になる
   - 解決: より大きく視覚的に異なるパターンを持つPNG (16x16) を生成

2. **detect_layout系テスト**:
   - テストがページ別JSONファイル出力を想定していたが、実装は単一のlayout.json
   - 解決: テストのアサーションを実際の出力形式に合わせて修正

## 次フェーズへの引き継ぎ

### User Story 1 & 2 (US1, US2) 完了状態

- ✅ 全CLIに--limitオプション実装済み (Phase 2)
- ✅ 全基盤関数にlimitパラメータ実装済み (Phase 2)
- ✅ Makefileにtest-runターゲット実装済み (Phase 2)
- ✅ 後方互換性確認済み (Phase 3)
- ✅ エッジケース確認済み (Phase 3)
- ✅ 全テストがPASS (GREEN)

### Phase 4 (US3) への準備

Phase 4では以下を実装予定:
- バリデーションエラーテスト (tests/cli/test_limit_validation.py)
- `--limit 0` でエラー表示
- `--limit -1` でエラー表示
- `--limit abc` でargparseエラー

現在の実装は以下のバリデーションを持つ:
- `--limit` は `type=int` で定義済み → 非整数入力はargparseが自動でエラー
- ただし `--limit 0` や `--limit -1` は現在受け入れられている

Phase 4では各CLIに以下のバリデーションを追加する必要がある:
```python
if args.limit is not None and args.limit <= 0:
    parser.error("--limit must be a positive integer")
```

## 注意事項

- **実装変更なし**: Phase 3ではテストの修正のみ実施
- **テストデータの品質**: 知覚ハッシュテストでは視覚的に異なるパターンを持つ画像が必要
- **detect_layoutの出力形式**: 単一のlayout.jsonファイルに全ページのデータを格納

## 備考

- 全変更ファイルに対して `ruff check --fix` と `ruff format` を実行済み
- REDテストで検出された問題はテストデータとアサーションの問題であり、実装の品質を証明
- Phase 2で実装された`--limit`機能は設計通り正しく動作している
