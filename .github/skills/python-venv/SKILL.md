---
name: python-venv
description: How to use the project Python virtual environment when running Python commands directly. USE FOR: running a Python script or command that has no make target; activating the venv manually; understanding which Python binary to use; troubleshooting "module not found" errors when running python directly. DO NOT USE FOR: tasks that already have a make target (use the use-makefile skill instead).
---

# Python Virtual Environment

Always run Python using the project's virtual environment.
If the task you need has a `make` target, use that instead — `make` activates the venv automatically.
Only drop into the venv manually when no `make` target exists.

## Virtual Environment Location

The Makefile auto-discovers the venv in this order:

1. `.venv/` (default, created by `make setup`)
2. `venv/`
3. `env/`
4. `$VIRTUAL_ENV` (if already activated in the shell)

The venv is almost always at `.venv/` unless you created it manually elsewhere.

## Activating the Virtual Environment

```bash
# Activate (standard)
source .venv/bin/activate

# Deactivate when done
deactivate
```

Once activated, `python` and `pip` resolve to the venv binaries automatically.

## Running a Single Command Without Activating

Prefer this pattern to avoid forgetting to deactivate:

```bash
# Run a script
.venv/bin/python path/to/script.py

# Run a module
.venv/bin/python -m pytest tests/

# Install a package (prefer make targets instead)
.venv/bin/pip install some-package
```

## First-Time Setup

If `.venv/` does not exist yet:

```bash
make setup-full   # Recommended for contributors
# or
make setup        # Basic setup
```

Never create the venv manually with `python -m venv` — use `make setup` so the Makefile uses the correct Python version.

## Checking Which Python Is Active

```bash
# Should point inside .venv/
which python
python --version
```

## Common Issues

| Problem | Fix |
| ------- | --- |
| `ModuleNotFoundError` | You are using the system Python, not the venv. Activate it first. |
| `command not found: python` | Use `python3`, or activate the venv. |
| `.venv/` missing | Run `make setup` to create it. |
| Wrong Python version | Run `make check-python` to verify compatibility. |
