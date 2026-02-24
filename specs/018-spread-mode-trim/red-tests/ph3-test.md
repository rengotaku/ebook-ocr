# Phase 3 RED Tests: 2段階 Trim 制御

**Date**: 2026-02-24
**Status**: RED (FAIL verified)
**User Story**: US2 - 2段階 Trim 制御

## サマリ

| 項目 | 値 |
|------|-----|
| 作成テスト数 | 39 |
| FAIL 数 | 39 (ImportError によりコレクション段階で全て失敗) |
| テストファイル | tests/preprocessing/test_split_spread.py |

## テストクラス構成

| クラス | テスト数 | 対象タスク | 概要 |
|--------|----------|------------|------|
| TestGlobalTrimTopBottom | 5 | T031 | global-trim-top/bottom の適用と高さ変化の検証 |
| TestGlobalTrimLeftRight | 6 | T032 | global-trim-left/right の適用と幅変化の検証 |
| TestTrimOrdering | 5 | T033 | global-trim -> split-trim の適用順序の検証 |
| TestSingleModeGlobalTrim | 4 | T034 | 単ページモードでの global-trim 適用 |
| TestTrimValidation | 11 | T035 | trim 値の範囲検証 (0.0 <= x < 0.5) |
| TestTrimEdgeCases | 8 | - | エッジケース (不変性、None入力、小画像、大画像、複数画像) |

## 失敗テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|----------|
| test_split_spread.py | TestGlobalTrimTopBottom::test_global_trim_top_reduces_height | top 2% トリムで高さ 500->490 |
| test_split_spread.py | TestGlobalTrimTopBottom::test_global_trim_bottom_reduces_height | bottom 2% トリムで高さ 500->490 |
| test_split_spread.py | TestGlobalTrimTopBottom::test_global_trim_top_and_bottom_combined | top+bottom 2% で高さ 500->480 |
| test_split_spread.py | TestGlobalTrimTopBottom::test_global_trim_top_removes_top_border | 赤い上端ボーダーがトリムされる |
| test_split_spread.py | TestGlobalTrimTopBottom::test_global_trim_zero_top_bottom_no_change | 0.0 指定で変化なし |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_left_reduces_width | left 1% トリムで幅 1000->990 |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_right_reduces_width | right 1% トリムで幅 1000->990 |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_left_and_right_combined | left+right 1% で幅 1000->980 |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_all_sides | 4辺すべてトリム 980x480 |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_left_removes_left_border | 緑の左端ボーダーがトリムされる |
| test_split_spread.py | TestGlobalTrimLeftRight::test_global_trim_zero_all_no_change | 全0でサイズ不変 |
| test_split_spread.py | TestTrimOrdering::test_global_trim_then_split_produces_correct_width | global trim 後に分割で各半分 900px |
| test_split_spread.py | TestTrimOrdering::test_global_trim_then_split_trim_combined | global+split trim で 810px |
| test_split_spread.py | TestTrimOrdering::test_global_trim_top_bottom_then_split_preserves_height | top/bottom trim 後の分割で高さ 800 |
| test_split_spread.py | TestTrimOrdering::test_split_trim_not_applied_without_global_trim | split-trim のみで 900px |
| test_split_spread.py | TestTrimOrdering::test_default_trim_config_no_trimming | デフォルト TrimConfig でトリムなし |
| test_split_spread.py | TestSingleModeGlobalTrim::test_single_mode_applies_global_trim | single モードでも global-trim 適用 |
| test_split_spread.py | TestSingleModeGlobalTrim::test_single_mode_global_trim_all_sides | single モードで 4辺トリム |
| test_split_spread.py | TestSingleModeGlobalTrim::test_single_mode_split_trim_ignored | single モードで split-trim 無視 |
| test_split_spread.py | TestSingleModeGlobalTrim::test_single_mode_no_trim_config_preserves_original | trim_config なしでサイズ不変 |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_zero_valid | 0.0 は有効 |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_small_valid | 0.01 は有効 |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_just_below_half_valid | 0.49 は有効 |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_half_invalid | 0.5 で ValueError |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_above_half_invalid | 0.8 で ValueError |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_one_invalid | 1.0 で ValueError |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_negative_invalid | -0.1 で ValueError |
| test_split_spread.py | TestTrimValidation::test_validate_trim_value_field_name_in_error | エラーにフィールド名含む |
| test_split_spread.py | TestTrimValidation::test_trim_config_validates_on_creation | TrimConfig(global_top=0.6) で ValueError |
| test_split_spread.py | TestTrimValidation::test_trim_config_validates_negative_on_creation | TrimConfig(global_left=-0.01) で ValueError |
| test_split_spread.py | TestTrimValidation::test_trim_config_validates_all_fields | 全フィールド検証 |
| test_split_spread.py | TestTrimEdgeCases::test_trim_config_default_all_zeros | デフォルト値がすべて 0.0 |
| test_split_spread.py | TestTrimEdgeCases::test_apply_global_trim_returns_new_image | 新しい Image を返す (不変性) |
| test_split_spread.py | TestTrimEdgeCases::test_apply_global_trim_with_none_raises | None 入力でエラー |
| test_split_spread.py | TestTrimEdgeCases::test_apply_global_trim_very_small_image | 10x10 画像でも動作 |
| test_split_spread.py | TestTrimEdgeCases::test_apply_global_trim_large_image | 4000x3000 大画像で動作 |
| test_split_spread.py | TestTrimEdgeCases::test_trim_config_with_unicode_special_chars_in_error | 特殊文字フィールド名 |
| test_split_spread.py | TestTrimEdgeCases::test_global_trim_preserves_image_mode | RGB モード保持 |
| test_split_spread.py | TestTrimEdgeCases::test_global_trim_with_spread_multiple_images | 複数画像に global-trim 適用 |

## 実装ヒント

- `TrimConfig`: `@dataclass` で global_top/bottom/left/right + left_page_outer/right_page_outer の 6 フィールド、全デフォルト 0.0
- `validate_trim_value(value: float, field_name: str)`: 0.0 <= value < 0.5 の範囲検証、フィールド名をエラーメッセージに含む
- `TrimConfig.__post_init__()`: 全フィールドに対して validate_trim_value を呼び出す
- `apply_global_trim(img: Image, trim_config: TrimConfig) -> Image`: `img.crop()` で新しい Image を返す（元画像を変更しない）
- `split_spread_pages()`: 新しい `trim_config: TrimConfig | None` 引数を追加、global-trim を split の前に適用
- split-trim (left_page_outer/right_page_outer) は mode=SPREAD のときのみ適用
- global-trim は mode=SINGLE でも適用される

## make test 出力 (抜粋)

```
ERRORS
__________ ERROR collecting tests/preprocessing/test_split_spread.py ___________
ImportError while importing test module 'tests/preprocessing/test_split_spread.py'.
tests/preprocessing/test_split_spread.py:23: in <module>
    from src.preprocessing.split_spread import (
E   ImportError: cannot import name 'TrimConfig' from 'src.preprocessing.split_spread'
=========================== short test summary info ============================
ERROR tests/preprocessing/test_split_spread.py
1 error in 0.36s
```

## 既存テストへの影響

- 既存テスト (`tests/test_split_spread.py`): 20 テスト全て PASS (影響なし)
- その他全テスト: 1341 passed, 6 skipped (リグレッションなし)
- Phase 2 テスト (同一ファイル内): ImportError により Phase 3 テストと共に収集不可（GREEN 実装後に復旧予定）
