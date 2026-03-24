---
name: cleanup
description: Repo cleanup workflow for dead code removal, stale comment cleanup, naming consistency, redundant code reduction, and safe maintainability improvements. USE FOR: requests like "clean up", maintenance passes, removing unused imports or variables, pruning TODOs, and replacing inappropriate production print statements. DO NOT USE FOR: speculative rewrites, major architecture changes, or broad dependency upgrades.
argument-hint: "[target file, folder, or cleanup scope]"
---

# Cleanup Workflow

Use this skill when the request is broad but the expected outcome is a safe,
behavior-preserving maintenance pass.

## Primary Goals

- Remove unused imports, locals, helper functions, and classes when they are truly unreferenced.
- Remove commented-out code and stale TODO or FIXME comments.
- Replace `print` in production application code with `get_logger(__name__)` when logging is appropriate.
- Keep user-facing `print` output in standalone scripts or tooling when it is intentional.
- Simplify obvious duplication, reduce needless complexity, and standardize naming where it improves clarity.

## Repo-Specific Guardrails

- Use `make` targets instead of raw commands whenever a target exists.
- Default validation flow for Python code changes:

```bash
make format
make lint
make test-unit
```

- If Markdown files change, also run:

```bash
make lint-markdown
```

- Do not upgrade dependencies, split modules, or reorganize directories unless there is clear evidence that the cleanup requires it.
- Treat "tree shaking" as Python dead-code elimination, not JavaScript bundle optimization.
- Preserve public behavior unless the user explicitly asks for a breaking cleanup.

## Execution Pattern

1. Inspect the target files and their tests before editing.
2. Use static-analysis findings and references to confirm imports, variables, functions, and classes are unused before deleting them.
3. Prefer small, local refactors over sweeping rewrites.
4. Add or update focused tests if the cleanup materially changes control flow.
5. Report what was removed, what was intentionally left alone, and any risks that still need manual review.

## What "Cleanup" Usually Includes Here

- Unused imports and locals
- Dead helpers and dead classes
- Commented-out code
- Stale TODO or FIXME notes
- Production `print` statements that should be logging
- Small duplicate blocks that can be consolidated safely
- Overly repetitive or noisy naming

## What It Usually Does Not Include

- Dependency version bumps
- Large-scale file splits
- Public API redesign
- New feature work disguised as cleanup

## Example Invocations

```text
/cleanup mealie_translate/recipe_processor.py
/cleanup repo-wide dead code pass excluding tools/
/cleanup remove stale TODOs and inappropriate print statements
```
