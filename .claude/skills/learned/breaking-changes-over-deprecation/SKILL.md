---
name: breaking-changes-over-deprecation
description: "When refactoring personal/local projects, prefer complete removal over deprecation to reduce maintenance burden"
---

# Breaking Changes Over Deprecation

## Problem

When cleaning up code, the default approach is to maintain backward compatibility:
- Add [DEPRECATED] comments
- Keep legacy aliases
- Maintain old targets/functions

This creates ongoing maintenance burden for no benefit in personal/local projects.

## Solution

For personal/local projects, prefer breaking changes:

1. **Remove completely** instead of deprecating
2. **Delete legacy targets** instead of hiding from help
3. **Remove unused variables** instead of commenting out
4. **Update documentation** to reflect removals

## When to Use

- Personal or local-only projects
- Active development (not abandoned codebase)
- Clear ownership (no external consumers)
- Issue/PR documents the breaking changes

## When NOT to Use

- Public libraries with external users
- Shared infrastructure
- APIs consumed by other teams
