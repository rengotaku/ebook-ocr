# video-separater Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-04

## Active Technologies
- Python 3.13+ (Constitution準拠) (002-book-md-structure)
- ファイルベース（入力: book.md, 出力: book.xml） (002-book-md-structure)
- Python 3.13+ + xml.etree.ElementTree（標準ライブラリ）, re（正規表現） (003-heading-readaloud-rules)
- 設定ファイル（パターン定義）はYAMLまたはJSON形式 (003-heading-readaloud-rules)
- Python 3.13+ (Constitution準拠) + xml.etree.ElementTree（標準ライブラリ）, re（正規表現） (004-toc-structure)
- ファイルベース（入力: book.xml, 出力: book.xml） (005-toc-page-grouping)
- Python 3.13+ + doclayout-yolo, Pillow, requests, pyyaml (007-layout-region-ocr)
- ファイルベース（layout.json, book.txt, book.md） (007-layout-region-ocr)
- Python 3.13+ + yomitoku>=0.10.0, paddleocr>=2.7.0, easyocr>=1.7.0, opencv-python (CLAHE用), difflib (文字アライメント) (008-rover-redesign)
- ファイルベース（raw/{engine}/, rover/） (008-rover-redesign)
- ファイルベース（入力: book.md, 出力: book.xml, figures/） (009-converter-redesign)

- Python 3.13+ + Pillow, imagehash, doclayout-yolo, requests (001-code-refactoring)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.13+: Follow standard conventions

## Recent Changes
- 009-converter-redesign: Added Python 3.13+ + xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
- 008-rover-redesign: Added Python 3.13+ + yomitoku>=0.10.0, paddleocr>=2.7.0, easyocr>=1.7.0, opencv-python (CLAHE用), difflib (文字アライメント)
- 007-layout-region-ocr: Added Python 3.13+ + doclayout-yolo, Pillow, requests, pyyaml


<!-- MANUAL ADDITIONS START -->

## Speckit Framework

This project uses the Speckit framework for specification-driven development.

### Available Commands

- `/speckit.specify` - Create or update feature specification
- `/speckit.clarify` - Identify and resolve underspecified areas
- `/speckit.plan` - Generate implementation plan
- `/speckit.tasks` - Generate actionable tasks
- `/speckit.checklist` - Create custom checklist
- `/speckit.analyze` - Analyze cross-artifact consistency
- `/speckit.implement` - Execute implementation plan
- `/speckit.constitution` - Manage project constitution
- `/speckit.taskstoissues` - Convert tasks to GitHub issues

### Directory Structure

```
.specify/
  scripts/bash/     # Bash helper scripts
  templates/        # Specification templates
  memory/           # Agent memory files
.claude/
  agents/           # Subagents (phase-executor, tdd-generator)
  commands/         # Speckit command definitions
specs/              # Feature specifications
```

### Workflow

1. **Specify**: Define feature requirements with `/speckit.specify`
2. **Clarify**: Resolve ambiguities with `/speckit.clarify`
3. **Plan**: Create implementation plan with `/speckit.plan`
4. **Tasks**: Generate tasks with `/speckit.tasks`
5. **Implement**: Execute with `/speckit.implement`
6. **Analyze**: Verify consistency with `/speckit.analyze`

## CRITICAL: No Hardcoded Domain-Specific Values

**書籍構造（chapter, section, episode等）をハードコードするな。**

書籍ごとに構造は異なる。今日の書籍が「Chapter」を使っていても、明日の書籍は「第N章」や「Episode」を使う。

### 絶対に禁止

```python
# これは糞コード
if re.match(r'^Chapter\s+(\d+)', text):  # ハードコード
if re.match(r'^第(\d+)章', text):        # ハードコード
level = "chapter"                         # ハードコード
```

### 正しい実装

```python
# CLI引数で設定を受け取る
--header-level1=chapter
--header-level2=episode|column

# 設定駆動で動的にパターン生成
for keyword in config.get_keywords_for_level(level):
    pattern = rf'^{re.escape(keyword)}\s*(\d+)'
```

### 原則

1. **ドメイン固有の値は外部設定化**: CLI引数、設定ファイル、環境変数
2. **後方互換性のためのフォールバックは不要**: 古い糞コードを残すな
3. **「今回だけ」のハードコードは次回の負債**: 最初から設定駆動で作れ

<!-- MANUAL ADDITIONS END -->
