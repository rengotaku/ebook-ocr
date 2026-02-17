# Data Model: パイプライン・リファクタリング

**Date**: 2026-02-17
**Feature**: 010-pipeline-refactoring

## Overview

このリファクタリングでは新しいデータモデルを導入しない。既存の中間ファイル形式を維持しつつ、処理フローを明確化する。

## Intermediate File Types

### 1. フレーム画像

**Location**: `{output_dir}/frames/`
**Format**: PNG
**Naming**: `frame_{number:05d}.png`

### 2. ページ画像（重複除去後）

**Location**: `{output_dir}/pages/`
**Format**: PNG
**Naming**: `page_{number:03d}.png`

### 3. レイアウト情報

**Location**: `{output_dir}/layout/`
**Format**: JSON
**Structure**:
```json
{
  "page": "page_001.png",
  "regions": [
    {
      "type": "TEXT|FIGURE|TABLE",
      "bbox": [x1, y1, x2, y2],
      "confidence": 0.95
    }
  ]
}
```

### 4. OCR結果

**Location**: `{output_dir}/ocr_output/`
**Format**: JSON per page
**Structure**:
```json
{
  "page": "page_001.png",
  "text": "...",
  "confidence": 0.92,
  "engine": "rover"
}
```

### 5. 統合出力

**Location**: `{output_dir}/`
**Files**:
- `book.txt`: プレーンテキスト
- `book.md`: Markdown形式

## Data Flow

```
video.mp4
    │
    ▼ [extract_frames]
frames/frame_*.png
    │
    ▼ [deduplicate]
pages/page_*.png
    │
    ▼ [split_spreads] (optional)
pages/page_*.png (renumbered)
    │
    ▼ [detect_layout]
layout/*.json
    │
    ▼ [run_ocr]
ocr_output/*.json
    │
    ▼ [consolidate]
book.txt, book.md
```

## Entity Relationships

```
Video (1) ─────────────> (N) Frames
                              │
                              ▼
                         (M) Pages (M <= N, after dedup)
                              │
                              ▼
                         (M) Layouts
                              │
                              ▼
                         (M) OCR Results
                              │
                              ▼
                         (1) Book Output
```

## Validation Rules

- フレーム番号は連続した整数
- ページ番号は重複除去・分割後に再採番
- レイアウトJSONは対応するページ画像が存在すること
- OCR結果JSONは対応するページ画像が存在すること

## No New Models Required

このリファクタリングでは:
- 新しいデータベースなし
- 新しいデータ構造なし
- ファイル形式の変更なし

既存の中間ファイル形式を維持し、処理を独立したスクリプトに分解するのみ。
