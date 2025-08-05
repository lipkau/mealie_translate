# GitHub Scripts

This directory contains utility scripts used by GitHub workflows.

## filter_sarif.py

**Purpose**: Filter SARIF (Static Analysis Results Interchange Format) files to remove false positives and low-severity findings.

**Usage**:

```bash
python filter_sarif.py input.sarif output.sarif
```

**What it filters**:

- Common false positives for simple Python applications
- Rules not applicable to our API-only application (SQL injection, XSS, etc.)
- Low-severity findings (info, note level)
- Results from test files, documentation, and configuration files

**Used by**: CodeQL workflow (`.github/workflows/codeql.yml`) to reduce noise in security scanning results.

**Benefits**:

- Dramatically reduces false positive alerts
- Focuses security team attention on real issues
- Maintains comprehensive security coverage for applicable threats
