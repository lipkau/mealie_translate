---
name: write-documentation
description: Rules and workflow for writing and editing project documentation. USE FOR: creating or updating Markdown files in docs/; checking documentation style; understanding line-length limits; writing headings, code blocks, or links correctly; running markdownlint. DO NOT USE FOR: writing code comments or docstrings; general coding tasks.
argument-hint: "[doc file or section to write/update]"
---

# Writing Documentation

This project enforces consistent documentation style via `markdownlint`.
Always lint documentation before committing.

## Linting

```bash
make lint-markdown     # Run markdownlint (requires npm install)
npm install            # Install Node.js deps if not already done
```

The markdownlint configuration is in [`.markdownlint-cli2.jsonc`](../../../.markdownlint-cli2.jsonc).

When the request is simply "update documentation", treat that as a docs-sync task:

- Update the relevant files in `docs/`, `README.md`, or contributor-facing guidance.
- Keep examples and commands aligned with the current code and Makefile targets.
- If a new doc file is added, include it in [`docs/README.md`](../../../docs/README.md).

## Style Rules

### Line Length

Maximum **120 characters** per line (code blocks and tables are exempt).
Write **one sentence per line** — this produces cleaner git diffs.

```markdown
<!-- ✓ GOOD -->
This sentence explains the concept clearly.
This is a separate sentence on its own line.

<!-- ✗ BAD -->
This sentence explains the concept clearly. This is a separate sentence that makes the line too long and harder to diff.
```

### Headings

- No trailing punctuation in headings.
- No duplicate headings at the same nesting level (siblings only).

```markdown
<!-- ✓ GOOD -->
## Setup

<!-- ✗ BAD -->
## Setup:
```

### Code Blocks

Always specify the language after the opening fence.

```markdown
<!-- ✓ GOOD -->
```bash
make test-unit
```

<!-- ✗ BAD -->
```
make test-unit
```
```

### Links

Use descriptive link text. Bare URLs are allowed (they will not trigger `no-bare-urls`).

```markdown
<!-- ✓ GOOD -->
See the [development guide](DEVELOPMENT.md) for details.
https://example.com is also fine as bare URL.

<!-- ✗ BAD -->
Click [here](DEVELOPMENT.md).
```

### Tables

Tables are exempt from the line-length limit. Use them freely for structured data.

## Doc Index

When adding a new documentation file, add an entry to [`docs/README.md`](../../../docs/README.md).

## Checklist Before Committing Docs

1. Run `make lint-markdown` and fix all errors.
2. Verify line length ≤ 120 chars (tables and code blocks excluded).
3. Check that new files are listed in `docs/README.md`.
4. Confirm code examples actually work.
