---
name: semantic-commits
description: >-
  Write descriptive conventional commit messages that explain intent. USE FOR:
  committing changes; reviewing staged diffs; drafting commit messages; when
  the user asks to commit. DO NOT USE FOR: general coding; writing tests;
  deployment.
---

# Semantic Commits

Every commit in this project uses the
[Conventional Commits](https://www.conventionalcommits.org/) format.
Messages must be descriptive — explain **why** the change was made, not just
what changed.

## Format

```text
<type>(<scope>): <subject>

[optional body]

[optional footer(s)]
```

### Type (required)

| Type       | When to use                                      |
| ---------- | ------------------------------------------------ |
| `feat`     | New user-facing feature or capability             |
| `fix`      | Bug fix                                           |
| `docs`     | Documentation only (Markdown, docstrings, comments) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test`     | Adding or updating tests                          |
| `ci`       | CI/CD pipeline or workflow changes                |
| `chore`    | Maintenance (deps, build scripts, tooling)        |

### Scope (recommended)

A short noun identifying the area of the codebase. Use the scopes that
already appear in the git log when they fit:

```text
translator, organizer, converter, docker, cd, ci, deps, makefile,
security, http, tools, skills
```

Add a new scope only when none of the above applies.

### Subject line rules

1. Use **imperative mood** ("add", not "added" or "adds").
2. Do **not** capitalize the first word after the colon.
3. Do **not** end with a period.
4. Keep to **72 characters** or fewer.
5. Describe **intent**, not mechanics:
   - Good: `fix(converter): handle fractional cups in metric conversion`
   - Bad: `fix(converter): change if statement`

### Body (when needed)

Add a body for any commit where the subject alone does not explain:

- **Why** the change was necessary.
- **What** trade-offs or alternatives were considered.
- **How** the change achieves its goal, if non-obvious.

Wrap body lines at 72 characters. Separate from the subject with a blank
line.

### Breaking changes

Append `!` after the type/scope **and** add a `BREAKING CHANGE:` footer:

```text
feat(translator)!: require API key via environment variable

BREAKING CHANGE: the --api-key CLI flag has been removed;
set OPENAI_API_KEY instead.
```

## Commit workflow

When the user asks you to commit:

1. Run `git diff --cached` (and `git status`) to understand staged changes.
2. Read recent commits (`git log --oneline -10`) to match the project's
   existing voice and scope conventions.
3. Classify the change using the type table above.
4. Draft a subject line that answers "**why** does this change exist?"
5. Add a body if the subject alone is insufficient.
6. Use a HEREDOC to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
feat(translator): support DeepL as an alternative backend

Add a --backend flag that accepts "openai" (default) or "deepl".
The DeepL provider reuses the same async HTTP client pool.
EOF
)"
```

## Examples from this repository

```text
fix(cd): use git ancestry check for prod builds instead of head_branch
feat(http): enable HTTP/2 for improved request performance (#41)
refactor(tools): extract shared model comparison fixtures
docs(skills): expand GitHub deployment skill with release plan (#50)
chore(deps): upgrade to Python 3.14 and Node.js 24 (#43)
test(converter): add comprehensive unit converter tests
ci(deps): bump dorny/test-reporter in the github-actions group (#45)
```
