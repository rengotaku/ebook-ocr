#!/bin/bash
# Session analyzer: Generate human-readable + Claude-analyzable report
# Usage: analyze-session.sh [session_id] [--json]

set -euo pipefail

# Detect session
if [[ -n "${1:-}" && "$1" != "--"* ]]; then
  SESSION_ID="$1"
  shift
else
  # Find most recent session in current project
  PROJECT_DIR=$(pwd)
  PROJECT_HASH=$(echo "$PROJECT_DIR" | sed 's|/|-|g; s|^-||')
  SESSION_DIR="$HOME/.claude/projects/$PROJECT_HASH"
  SESSION_FILE=$(ls -t "$SESSION_DIR"/*.jsonl 2>/dev/null | grep -v 'agent-' | head -1)
  SESSION_ID=$(basename "$SESSION_FILE" .jsonl)
fi

OUTPUT_JSON="${1:-}"
SESSION_DIR="$HOME/.claude/projects/-home-takuya-dotfiles"
SESSION_FILE="$SESSION_DIR/$SESSION_ID.jsonl"
SUBAGENT_DIR="$SESSION_DIR/$SESSION_ID/subagents"

if [[ ! -f "$SESSION_FILE" ]]; then
  echo "Session not found: $SESSION_ID"
  exit 1
fi

# ============================================================
# Data extraction
# ============================================================

# Session metadata
START_TIME=$(jq -s '.[0].timestamp' "$SESSION_FILE" | tr -d '"')
END_TIME=$(jq -s '.[-1].timestamp' "$SESSION_FILE" | tr -d '"')

# Tool usage (main session)
MAIN_TOOLS=$(jq -s '
  [.[] | select(.type == "assistant") | .message.content |
   if type == "array" then .[] else . end |
   select(.name?) | {name, input}]
' "$SESSION_FILE")

# File operations
FILE_OPS=$(echo "$MAIN_TOOLS" | jq '
  [.[] | select(.name == "Read" or .name == "Edit" or .name == "Write") |
   {tool: .name, file: .input.file_path}]
')

# Bash commands
BASH_CMDS=$(echo "$MAIN_TOOLS" | jq '
  [.[] | select(.name == "Bash") | .input.command]
')

# Errors
ERRORS=$(jq -s '
  [.[] | select(.type == "user") | .message.content |
   if type == "array" then .[] else empty end |
   select(.type? == "tool_result" and .is_error == true) |
   .content]
' "$SESSION_FILE")

# Subagents (detailed)
SUBAGENTS="[]"
if [[ -d "$SUBAGENT_DIR" ]] && ls "$SUBAGENT_DIR"/*.jsonl >/dev/null 2>&1; then
  SUBAGENTS=$(
    for f in "$SUBAGENT_DIR"/*.jsonl; do
      [[ -f "$f" ]] || continue
      jq -s '
        {
          id: (.[0].agentId // "unknown"),
          slug: (.[0].slug // "unknown"),
          prompt: ((.[0].message.content // "unknown") | if type == "string" then .[0:100] else tostring[0:100] end),
          model: ([.[] | select(.type == "assistant") | .message.model][0] // "unknown"),
          tokens: {
            input: ([.[] | select(.type == "assistant") | .message.usage.input_tokens // 0] | add),
            output: ([.[] | select(.type == "assistant") | .message.usage.output_tokens // 0] | add),
            cache_read: ([.[] | select(.type == "assistant") | .message.usage.cache_read_input_tokens // 0] | add)
          },
          tool_calls: [
            .[] | select(.type == "assistant") | .message.content |
            if type == "array" then .[] else . end |
            select(.name?) |
            {
              tool: .name,
              detail: (
                if .name == "Bash" then .input.command[0:80]
                elif .name == "Read" then .input.file_path
                elif .name == "Edit" then .input.file_path
                elif .name == "Write" then .input.file_path
                elif .name == "WebFetch" then .input.url
                elif .name == "Grep" then .input.pattern
                elif .name == "Glob" then .input.pattern
                elif .name == "Task" then .input.description
                else (.input | tostring)[0:60]
                end
              )
            }
          ],
          errors: [
            .[] | select(.type == "user") | .message.content |
            if type == "array" then .[] else empty end |
            select(.type? == "tool_result" and .is_error == true) |
            .content[0:100]
          ],
          start_time: .[0].timestamp,
          end_time: .[-1].timestamp
        }
      ' "$f"
    done | jq -s '.'
  )
fi

# Tool summary
TOOL_SUMMARY=$(echo "$MAIN_TOOLS" | jq '
  group_by(.name) | map({tool: .[0].name, count: length}) | sort_by(-.count)
')

# ============================================================
# Output
# ============================================================

if [[ "$OUTPUT_JSON" == "--json" ]]; then
  # JSON output for Claude analysis
  jq -n \
    --arg session_id "$SESSION_ID" \
    --arg start "$START_TIME" \
    --arg end "$END_TIME" \
    --argjson tool_summary "$TOOL_SUMMARY" \
    --argjson file_ops "$FILE_OPS" \
    --argjson bash_cmds "$BASH_CMDS" \
    --argjson errors "$ERRORS" \
    --argjson subagents "$SUBAGENTS" \
    '{
      session_id: $session_id,
      duration: {start: $start, end: $end},
      tool_summary: $tool_summary,
      file_operations: $file_ops,
      bash_commands: $bash_cmds,
      errors: $errors,
      subagents: $subagents
    }'
  exit 0
fi

# Human-readable output
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    SESSION ANALYSIS REPORT                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Session: $SESSION_ID"
echo "⏱️  Start:   $START_TIME"
echo "⏱️  End:     $END_TIME"
echo ""

echo "┌──────────────────────────────────────────────────────────────┐"
echo "│ 🔧 Tool Usage Summary                                        │"
echo "└──────────────────────────────────────────────────────────────┘"
echo "$TOOL_SUMMARY" | jq -r '.[] | "  \(.tool): \(.count)"'
echo ""

echo "┌──────────────────────────────────────────────────────────────┐"
echo "│ 📁 File Operations                                           │"
echo "└──────────────────────────────────────────────────────────────┘"
echo "$FILE_OPS" | jq -r '.[] | "  [\(.tool)] \(.file)"' | sort | uniq -c | sort -rn | head -20
echo ""

echo "┌──────────────────────────────────────────────────────────────┐"
echo "│ 💻 Bash Commands (top 10)                                    │"
echo "└──────────────────────────────────────────────────────────────┘"
echo "$BASH_CMDS" | jq -r '.[]' | head -10 | while read -r cmd; do
  echo "  $ ${cmd:0:70}"
done
echo ""

ERROR_COUNT=$(echo "$ERRORS" | jq 'length')
if [[ "$ERROR_COUNT" -gt 0 ]]; then
  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ ❌ Errors ($ERROR_COUNT)                                           │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "$ERRORS" | jq -r '.[]' | head -5 | while read -r err; do
    echo "  ${err:0:70}..."
  done
  echo ""
fi

SUBAGENT_COUNT=$(echo "$SUBAGENTS" | jq 'length')
if [[ "$SUBAGENT_COUNT" -gt 0 ]]; then
  echo "┌──────────────────────────────────────────────────────────────┐"
  echo "│ 🤖 Subagents ($SUBAGENT_COUNT)                                         │"
  echo "└──────────────────────────────────────────────────────────────┘"
  echo "$SUBAGENTS" | jq -r '
    .[] |
    "  \(.id) (\(.slug))",
    "    prompt: \(.prompt | if type == "string" then .[0:60] else "..." end)...",
    "    model: \(.model | split("-") | .[-1])",
    "    tokens: \(.tokens.input) in / \(.tokens.output) out (cache: \(.tokens.cache_read))",
    "    tools:",
    (.tool_calls[] | "      - [\(.tool)] \(.detail[0:50])"),
    (if (.errors | length) > 0 then "    ❌ errors: \(.errors | length)" else empty end),
    ""
  '
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Run with --json for Claude-analyzable output"
