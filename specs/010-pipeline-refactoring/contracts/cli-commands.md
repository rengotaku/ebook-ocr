# CLI Commands Contract

**Date**: 2026-02-17
**Feature**: 010-pipeline-refactoring

## Overview

各CLIコマンドの入出力仕様を定義する。全コマンドは独立して実行可能。

---

## 1. extract_frames

**Purpose**: 動画からフレームを抽出

**Usage**:
```bash
python -m src.cli.extract_frames VIDEO_PATH -o OUTPUT_DIR [OPTIONS]
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| VIDEO_PATH | path | Yes | - | 入力動画ファイルパス |
| -o, --output | path | Yes | - | フレーム出力ディレクトリ |
| -i, --interval | float | No | 1.5 | フレーム抽出間隔（秒） |

**Input**: 動画ファイル（.mp4, .mov, .avi等）
**Output**: `{output}/frame_{00000}.png`

**Exit Codes**:
- 0: 成功
- 1: 入力ファイル不存在
- 2: 出力ディレクトリ作成失敗

---

## 2. deduplicate

**Purpose**: 重複フレームを除去

**Usage**:
```bash
python -m src.cli.deduplicate INPUT_DIR -o OUTPUT_DIR [OPTIONS]
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| INPUT_DIR | path | Yes | - | フレーム入力ディレクトリ |
| -o, --output | path | Yes | - | ページ出力ディレクトリ |
| -t, --threshold | int | No | 8 | ハッシュ閾値 |

**Input**: `{input}/frame_*.png`
**Output**: `{output}/page_{000}.png`

**Exit Codes**:
- 0: 成功
- 1: 入力ディレクトリ不存在または空

---

## 3. split_spreads

**Purpose**: 見開きページを分割

**Usage**:
```bash
python -m src.cli.split_spreads PAGES_DIR [OPTIONS]
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| PAGES_DIR | path | Yes | - | ページディレクトリ（in-place更新） |
| --aspect-ratio | float | No | 1.2 | 見開き判定閾値 |
| --left-trim | float | No | 0.0 | 左ページ左端トリム率 |
| --right-trim | float | No | 0.0 | 右ページ右端トリム率 |

**Input/Output**: `{pages_dir}/page_*.png` (in-place更新、再採番)

**Exit Codes**:
- 0: 成功
- 1: 入力ディレクトリ不存在

---

## 4. detect_layout

**Purpose**: ページのレイアウトを検出

**Usage**:
```bash
python -m src.cli.detect_layout PAGES_DIR -o OUTPUT_DIR [OPTIONS]
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| PAGES_DIR | path | Yes | - | ページ画像ディレクトリ |
| -o, --output | path | Yes | - | レイアウト出力ディレクトリ |
| --device | choice | No | cpu | cpu または cuda |

**Input**: `{pages_dir}/page_*.png`
**Output**: `{output}/layout_{000}.json`

**Exit Codes**:
- 0: 成功
- 1: 入力ディレクトリ不存在
- 3: モデルロード失敗

---

## 5. run_ocr

**Purpose**: OCRを実行

**Usage**:
```bash
python -m src.cli.run_ocr PAGES_DIR -o OUTPUT_DIR [OPTIONS]
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| PAGES_DIR | path | Yes | - | ページ画像ディレクトリ |
| -o, --output | path | Yes | - | OCR結果出力ディレクトリ |
| --layout-dir | path | No | - | レイアウト情報ディレクトリ |
| --device | choice | No | cpu | cpu または cuda |

**Input**: `{pages_dir}/page_*.png`, `{layout_dir}/layout_*.json` (optional)
**Output**: `{output}/ocr_{000}.json`

**Exit Codes**:
- 0: 成功
- 1: 入力ディレクトリ不存在
- 3: OCRエンジン初期化失敗

---

## 6. consolidate

**Purpose**: OCR結果を統合

**Usage**:
```bash
python -m src.cli.consolidate OCR_DIR -o OUTPUT_DIR
```

**Arguments**:
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| OCR_DIR | path | Yes | - | OCR結果ディレクトリ |
| -o, --output | path | Yes | - | 出力ディレクトリ |

**Input**: `{ocr_dir}/ocr_*.json`
**Output**: `{output}/book.txt`, `{output}/book.md`

**Exit Codes**:
- 0: 成功
- 1: 入力ディレクトリ不存在または空

---

## Common Behaviors

### Error Messages

全コマンドは失敗時に標準エラー出力へメッセージを出力:
```
Error: {description}
```

### Verbose Mode

将来的に `--verbose` オプションを追加可能（現時点では未実装）。

### Configuration File

将来的に `--config` オプションでYAML設定ファイルを読み込み可能（現時点では未実装）。
