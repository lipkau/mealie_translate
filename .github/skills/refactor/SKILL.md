---
name: refactor
description: Behavior-preserving refactor workflow for simplifying logic, extracting smaller functions, consolidating duplication, and improving naming and structure. USE FOR: requests like "refactor", "simplify this module", or "break this function down". DO NOT USE FOR: feature work, speculative rewrites, or dependency-management tasks.
argument-hint: "[module, file, class, scripts, tests or function to refactor]"
---

# Refactor Workflow

Use this skill for targeted structural improvement when the goal is cleaner code
without changing external behavior.

## Refactor Priorities

- Break long functions into smaller helpers when the extraction improves readability.
- Reduce nesting and simplify complex branching.
- Consolidate duplicated logic into shared helpers when the abstraction is actually clearer.
- Standardize names when existing names are misleading or inconsistent.
- Keep the existing architecture unless there is a strong, code-backed reason to change it.

## Repo-Specific Rules

- This is a mature production project. Avoid oversimplifying infrastructure.
- Prefer minimal public API change. If an API must change, update all callers and tests in the same pass.
- Use `get_logger(__name__)` for production logging.
- Use `make` targets for validation.

## Default Validation Flow

```bash
make format
make lint
make test-unit
```

If documentation changes as part of the refactor, also run:

```bash
make lint-markdown
```

## Execution Pattern

1. Identify the specific pain points first: length, duplication, naming, or control-flow complexity.
2. Refactor in small, reviewable steps.
3. Preserve behavior while improving structure.
4. Add or update targeted tests if the refactor touches non-trivial logic.
5. Summarize what became simpler and any areas that still deserve a later pass.

## Good Prompt Shapes

- Mention the target path or symbol.
- State the main issue if known: long function, duplicate logic, confusing naming, or complex branching.
- Keep the request short; this skill supplies the workflow.

## Example Invocations

```text
/refactor mealie_translate/translator.py
/refactor simplify retry logic in mealie_translate/mealie_client.py
/refactor break down long functions in mealie_translate/recipe_processor.py
```
