# Phase 5 Output: US5 可視化・出力・設定外部化

**Date**: 2026-03-13
**Status**: Completed
**User Story**: US5 - CODE リージョンの可視化と出力 + 設定外部化

## 実行タスク

- [x] T078 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph5-test.md`
- [x] T079 `visualize_layout()` に `layout_regions` パラメータ追加 + CODE 黄色描画 in `src/layout/detector.py`
- [x] T080 `_format_region_summary()` ヘルパー関数を追加 in `src/layout/detector.py`
- [x] T081 `config.yaml` に `code_detection` セクションを追加（全8閾値のデフォルト値）
- [x] T082 `src/layout/code_detector.py` に `load_code_detection_config()` 関数を追加
- [x] T083 `make test` で PASS を確認 (GREEN)
- [x] T084 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T085 `make lint` で lint エラーなしを確認
- [x] T086 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph5-output.md`

## 変更ファイル

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `src/layout/detector.py` | 変更 | `_format_region_summary()` 追加、`visualize_layout()` に `layout_regions=None` パラメータ追加 + CODE 黄色描画 |
| `src/layout/code_detector.py` | 変更 | `load_code_detection_config()` 関数と `_DEFAULT_CODE_DETECTION_CONFIG` 定数を追加 |
| `config.yaml` | 変更 | `code_detection` セクションを追加（8キー・デフォルト値） |
| `tests/test_code_detector.py` | 変更 | `from pathlib import Path` インポートを追加（F821 修正）、ruff format による自動整形 |

## テスト結果

```
========= 1698 passed, 2 skipped, 131 deselected, 6 warnings in 33.90s =========
```

- Phase 5 RED テスト 21 件がすべて GREEN に転換
- Phase 2・3・4 テスト含む全テストのリグレッションなし
- lint: `make lint` パス（ruff check + ruff format + pylint --exit-zero）

**Coverage**: 計測対象外（make test のみ実行）

## 実装の詳細

### `_format_region_summary(regions)` 関数

- `src/layout/detector.py` に追加したヘルパー関数
- regions リストの合計数と CODE 型のカウントを集計
- `"{total} regions [CODE: {code_count}]"` 形式の文字列を返却
- テストが要求する `[CODE: N]` フォーマットに準拠

### `visualize_layout()` の変更

- `layout_regions=None` キーワード引数を追加（後方互換）
- `layout_regions` が提供された場合、各リージョンを走査
  - CODE: 黄色 (0, 255, 255) BGR
  - TITLE: 赤色 (0, 0, 255)
  - FIGURE: 青色 (255, 0, 0)
  - TEXT / その他: 緑色 (0, 255, 0)
- 既存の `paragraphs`/`figures` 描画ロジックはそのまま維持

### `load_code_detection_config(config_path=None)` 関数

- `src/layout/code_detector.py` に追加
- `config_path=None` の場合、プロジェクトルートの `config.yaml` を自動検索
- `code_detection` セクション不在・ファイル不在・例外の場合はデフォルト値を返却
- 部分設定: 未指定キーはデフォルト値で補完
- 型の強制変換: float/int キーに対して明示的キャストを適用

### `config.yaml` の追加セクション

```yaml
code_detection:
  gray_background_threshold: 0.7
  gray_saturation_max: 30
  gray_value_min: 50
  gray_value_max: 200
  aspect_ratio_max: 8.0
  symbol_ratio_threshold: 0.08
  keyword_threshold: 2
  fragment_gap_threshold: 80
```

## 発見した課題

1. **テストファイルの `Path` 未インポート**: Phase 5 RED テストで `tmp_path: "Path"` アノテーションが使用されていたが `from pathlib import Path` が欠落していた。`tests/test_code_detector.py` に追加して ruff F821 エラーを解消した。

## 次フェーズへの引き継ぎ

Phase 6（Polish & Cross-Cutting Concerns）で対応するもの:

- **確立したインターフェース**:
  - `visualize_layout()`: `layout_regions` パラメータ対応済み（後方互換維持）
  - `_format_region_summary()`: リージョンサマリ文字列生成
  - `load_code_detection_config()`: config.yaml からの設定読み込み
  - `config.yaml` の `code_detection` セクション: 全8閾値が外部設定化

- **Phase 6 で対応する作業**:
  - `src/layout/code_detector.py` のファイルサイズ確認と必要に応じた分割
  - 不要な import・デッドコードの削除
  - quickstart.md の手順確認

- **注意事項**:
  - `load_code_detection_config()` は追加されたが、既存の `detect_gray_background()` / `detect_code_by_text()` / `merge_code_fragments()` の呼び出し側で設定値を使用するよう統合する作業は未実施（テストが要求していないため）。Phase 6 での検討事項。
