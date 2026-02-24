# /speckit.analyze-session - Session Analysis for Speckit

Analyze the current session after `speckit.implement` completion.

## Instructions

1. Run the analysis script to get session data (prefer local, fallback to global):
   ```bash
   # Local (if exists)
   .specify/scripts/bash/analyze-session.sh [session_id] [--json]
   # Or global
   ~/.claude/scripts/analyze-session.sh [session_id] [--json]
   ```

2. Display the human-readable report to the user

3. If user requests improvement suggestions, run with `--json` flag and analyze:
   - Inefficient patterns (repeated file reads, redundant commands)
   - Error recovery patterns
   - Subagent utilization
   - Opportunities for parallelization

4. Reports are saved to `specs/<feature>/analyzed-action/` on session end

## Usage Examples

- `/speckit.analyze-session` - Analyze current session
- `/speckit.analyze-session --json` - Get JSON for deeper analysis
- `/speckit.analyze-session <session-id>` - Analyze specific session
