# video-separater Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-02-04

## Active Technologies
- Python 3.13+ (Constitution準拠) (002-book-md-structure)
- ファイルベース（入力: book.md, 出力: book.xml） (002-book-md-structure)
- Python 3.13+ + xml.etree.ElementTree（標準ライブラリ）, re（正規表現） (003-heading-readaloud-rules)
- 設定ファイル（パターン定義）はYAMLまたはJSON形式 (003-heading-readaloud-rules)
- Python 3.13+ (Constitution準拠) + xml.etree.ElementTree（標準ライブラリ）, re（正規表現） (004-toc-structure)

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
- 004-toc-structure: Added Python 3.13+ (Constitution準拠) + xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
- 003-heading-readaloud-rules: Added Python 3.13+ + xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
- 002-book-md-structure: Added Python 3.13+ (Constitution準拠)

- 001-code-refactoring: Added Python 3.13+ + Pillow, imagehash, doclayout-yolo, requests

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

<!-- MANUAL ADDITIONS END -->
