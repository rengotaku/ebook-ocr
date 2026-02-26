---
name: makefile-hash-comment-escape
description: "Fix Makefile errors when shell commands contain # character (sed patterns, comment stripping)"
---

# Makefile Hash Comment Escape

## Problem

Makefile内でsedコマンドを使ってYAMLコメントを除去しようとすると、`#` がMakeのコメント文字として解釈され、コマンドが途中で切れる。

```make
# これは壊れる - #以降がMakeコメントとして解釈される
CFG = grep '^$(1):' config.yaml | sed 's/[[:space:]]*#.*//'
```

**症状**:
```
/bin/bash: -c: line 1: unexpected EOF while looking for matching `''
```

## Root Cause

Makeは変数定義内でも `#` をコメント開始として解釈する。以下のエスケープ方法は**すべて失敗**:

- `\#` - 動作しない
- `[#]` - 文字クラス内でも解釈される
- `\043` (octal) - awkでは動くがsedでは複雑

## Solution

**方法1: Python + PyYAML (推奨)**

```make
CFG = python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(c.get('$(1)','') if c.get('$(1)') is not None else '')"
```

**方法2: 外部スクリプト**

```make
CFG = ./scripts/read-config.sh $(1)
```

## Example

Before (broken):
```make
SPREAD_MODE ?= $(shell grep '^spread_mode:' config.yaml | sed 's/.*: *//' | sed 's/#.*//')
# → 空になる
```

After (working):
```make
CFG = python3 -c "import yaml; c=yaml.safe_load(open('config.yaml')); print(c.get('$(1)',''))"
SPREAD_MODE ?= $(shell $(call CFG,spread_mode))
# → "single"
```

## When to Use

- Makefileでconfig/YAMLファイルからコメント付きの値を読み取る
- `unexpected EOF while looking for matching` エラーが出る
- シェルコマンドで `#` を含むパターンマッチが必要
