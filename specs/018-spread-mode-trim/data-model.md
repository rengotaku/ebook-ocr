# Data Model: Spread モード明示指定と Trim 制御の拡張

**Date**: 2026-02-24
**Feature**: 018-spread-mode-trim

## Entities

### SpreadMode (Enum)

画像の処理モードを表す。

| Value | Description |
|-------|-------------|
| `single` | 単ページモード - 画像を分割しない |
| `spread` | 見開きモード - 画像を左右2ページに分割 |

**Note**: `auto` モードは廃止。

### TrimConfig (Data Class)

トリミング設定を表す。

```python
@dataclass
class TrimConfig:
    # Global trim (分割前に適用)
    global_top: float = 0.0      # 上端トリム率 (0.0-0.5)
    global_bottom: float = 0.0   # 下端トリム率 (0.0-0.5)
    global_left: float = 0.0     # 左端トリム率 (0.0-0.5)
    global_right: float = 0.0    # 右端トリム率 (0.0-0.5)

    # Split trim (分割後に適用、spread モードのみ)
    left_page_outer: float = 0.0   # 左ページの左端トリム率
    right_page_outer: float = 0.0  # 右ページの右端トリム率
```

**Validation Rules**:
- すべての値は 0.0 <= x < 0.5 の範囲
- 0.5 以上はエラー（画像の半分以上をトリムすることになる）

### ProcessingConfig (Data Class)

処理全体の設定を表す。

```python
@dataclass
class ProcessingConfig:
    mode: SpreadMode = SpreadMode.SINGLE
    trim: TrimConfig = field(default_factory=TrimConfig)
    overlap_px: int = 0  # 中央のオーバーラップピクセル
```

### ProcessingResult (Data Class)

処理結果を表す。

```python
@dataclass
class ProcessingResult:
    input_path: Path           # 入力ファイルパス
    output_paths: list[Path]   # 出力ファイルパス（1つまたは2つ）
    mode_used: SpreadMode      # 使用されたモード
    trim_applied: TrimConfig   # 適用されたトリム設定
    was_split: bool            # 分割されたかどうか
```

## State Diagram

### 画像処理フロー

```
[入力画像]
    │
    ▼
[Global Trim 適用]
    │ global_top, global_bottom, global_left, global_right
    ▼
[モード判定]
    │
    ├─── mode=single ───▶ [出力: 1ファイル]
    │
    └─── mode=spread ───▶ [左右分割]
                              │
                              ▼
                         [Split Trim 適用]
                              │ left_page_outer, right_page_outer
                              ▼
                         [出力: 2ファイル]
```

### 設定優先順位

```
[CLI引数] ──▶ [環境変数] ──▶ [config.yaml] ──▶ [デフォルト値]
   優先度: 最高                                    最低
```

## File Structure

### 入力/出力ディレクトリ

```
output/<hash>/
├── pages/              # deduplicate の出力（処理対象）
├── originals/          # split-spreads のバックアップ
│   └── page_0001.png
├── preview/            # プレビュー用（NEW）
│   ├── frames/         # preview-extract の出力
│   │   └── page_0001.png
│   └── trimmed/        # preview-trim の出力
│       ├── page_0001_L.png
│       └── page_0001_R.png
└── ...
```

### 出力ファイル命名規則

| モード | 入力 | 出力 |
|--------|------|------|
| `single` | `page_0001.png` | `page_0001.png` |
| `spread` | `page_0001.png` | `page_0001_L.png`, `page_0001_R.png` |

## Configuration Schema

### config.yaml 追加項目

```yaml
# Spread splitting (見開き分割)
spread_mode: single           # 'single' または 'spread'（NEW）

# Global trim (分割前に適用)（NEW）
global_trim_top: 0.0
global_trim_bottom: 0.0
global_trim_left: 0.0
global_trim_right: 0.0

# Split trim (分割後に適用) - 既存項目
spread_left_trim: 0.0         # 左ページの左端
spread_right_trim: 0.0        # 右ページの右端
```

### 環境変数

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `SPREAD_MODE` | 処理モード | `single`, `spread` |
| `GLOBAL_TRIM_TOP` | 上端トリム率 | `0.02` |
| `GLOBAL_TRIM_BOTTOM` | 下端トリム率 | `0.02` |
| `GLOBAL_TRIM_LEFT` | 左端トリム率 | `0.01` |
| `GLOBAL_TRIM_RIGHT` | 右端トリム率 | `0.01` |
