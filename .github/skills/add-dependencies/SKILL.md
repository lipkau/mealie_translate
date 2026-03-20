---
name: add-dependencies
description: How to add Python or Node.js dependencies to this project. USE FOR: adding a new package; understanding where dependencies are declared; knowing what to run after adding a dependency; understanding how security scanning covers new dependencies. DO NOT USE FOR: general coding; writing tests; deployment.
argument-hint: "[package name and ecosystem: python or node]"
---

# Adding Dependencies

## Python Dependencies

Dependencies are declared in [`pyproject.toml`](../../../pyproject.toml).

### Runtime dependency (required by the application)

Add to the `[project]` `dependencies` list:

```toml
[project]
dependencies = [
    "requests>=2.31.0",
    "your-new-package>=1.0.0",   # ← add here
]
```

### Development-only dependency (testing, linting, tooling)

Add to `[project.optional-dependencies]` under `dev`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "your-dev-package>=1.0.0",   # ← add here
]
```

### After editing `pyproject.toml`:

```bash
make setup       # Reinstalls all dependencies into the venv
```

## Node.js Dependencies

Node.js is used only for documentation linting (`markdownlint`).
Declare packages in [`package.json`](../../../package.json), then run:

```bash
npm install
```

## Security

All Python dependencies are automatically scanned for known vulnerabilities by `pip-audit` in CI.
You can run the scan locally at any time:

```bash
make security-scan        # All security checks (bandit + pip-audit)
make security-pip-audit   # Dependency vulnerability scan only
```

Do not add a dependency with known high-severity CVEs.
If `pip-audit` reports an issue after adding a package, either pin a patched version or choose an alternative.
