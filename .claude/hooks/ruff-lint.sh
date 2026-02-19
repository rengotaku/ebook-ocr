#!/bin/bash
# ruff-lint.sh - Auto-lint Python files after edits

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only check Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Run ruff
if command -v ruff &> /dev/null; then
  ruff check --fix "$FILE_PATH" 2>&1 || true
  ruff format "$FILE_PATH" 2>&1 || true
fi

exit 0
