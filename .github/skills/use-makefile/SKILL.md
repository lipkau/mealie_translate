---
name: use-makefile
description: Guidance on using the project Makefile as the primary development interface. USE FOR: running tests, linting, formatting, security scans, or Docker commands; understanding which make target to use for a task; replacing raw commands with their make equivalents. DO NOT USE FOR: understanding the deployment pipeline; adding dependencies; writing documentation.
argument-hint: "[task you want to accomplish]"
---

# Using the Makefile

The `Makefile` is the **primary development interface** for this project.
Always prefer `make <target>` over running raw commands (pytest, ruff, python, docker, …) directly.
Run `make help` at any time to see the full, up-to-date list of targets.

## Why use `make`?

- Targets activate the virtual environment automatically.
- Targets set the correct flags, paths, and environment for each task.
- Targets are the same commands the CI pipeline uses — no surprises.

## Quick Reference

### Getting started

```bash
make help           # Full list of all targets with descriptions
make setup-full     # Complete developer setup (venv + deps + git hooks)
make setup          # Basic setup (venv + deps + .env)
```

### Day-to-day development cycle

```bash
make test-unit      # Fast unit tests (no external APIs) — run frequently
make format         # Auto-format code with ruff
make lint           # Check code quality (ruff + pyright)
make lint-all       # All checks: ruff + pyright + markdownlint
make check          # Full workflow: format + lint-all + test
```

### Testing

```bash
make test           # All tests (unit + integration)
make test-unit      # Unit tests only (fast, ~10-30 s)
make test-integration   # Integration tests (requires API keys in .env)
make test-coverage  # Tests + HTML/XML coverage reports
```

### Code quality & security

```bash
make lint-format    # Check formatting only
make lint-markdown  # Check documentation (requires npm install)
make security-scan  # All security scans (bandit + pip-audit)
```

### Docker

```bash
make docker-build   # Build the Docker image locally
make docker-run     # Run the container (cron mode)
make docker-dev     # Run development container
make docker-test    # Run tests inside Docker
make docker-logs    # Follow container logs
make docker-clean   # Remove Docker artifacts
```

### Running the application

```bash
make run            # Run the main application
```

### Cleanup

```bash
make clean          # Remove cache files and reports
make clean-all      # Deep clean including the virtual environment
```

## When a `make` target does not exist

If no target exists for what you need, run the raw command from within the activated virtual environment (see the `python-venv` skill).
Do **not** add a new target to the Makefile without checking that it does not duplicate an existing one.
