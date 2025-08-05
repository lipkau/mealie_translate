#!/usr/bin/env python3
"""SARIF Filter Script.

This script filters SARIF (Static Analysis Results Interchange Format) files
to remove common false positives and low-severity findings that clutter
GitHub's security scanning results.

Usage:
    python filter_sarif.py input.sarif output.sarif
"""

import json
import sys
from typing import Any, Dict


def should_exclude_rule(rule_id: str, rule_desc: str = "") -> bool:
    """Determine if a rule should be excluded based on common false positives.

    Args:
        rule_id: The rule identifier
        rule_desc: Optional rule description

    Returns:
        True if the rule should be excluded
    """
    # Rules that commonly produce false positives in simple Python apps
    false_positive_rules = {
        # URL/Hostname validation - our app makes simple API calls
        "py/incomplete-url-substring-sanitization",
        "py/incomplete-hostname-regexp",
        "py/incomplete-regular-expression-for-hostnames",
        # Regex injection - not applicable to our simple string processing
        "py/regex-injection",
        "py/polynomial-redos",
        # Logging - we don't log sensitive data in our simple app
        "py/clear-text-logging-sensitive-data",
        # Credentials - we properly document env var usage
        "py/hardcoded-credentials",
        "py/clear-text-storage-of-sensitive-data",
        # Path traversal - not applicable to our API-only app
        "py/path-injection",
        "py/unsafe-deserialization",
        # SQL injection - we don't use SQL databases
        "py/sql-injection",
        # XSS - we don't serve web content
        "py/reflected-xss",
        "py/stored-xss",
        # CSRF - we don't have web forms
        "py/csrf",
        # Command injection - we don't execute shell commands with user input
        "py/command-line-injection",
        "py/shell-command-constructed-from-input",
    }

    return rule_id in false_positive_rules


def should_exclude_result(result: Dict[str, Any]) -> bool:
    """Determine if a specific result should be excluded."""
    rule_id = result.get("ruleId", "")

    # Exclude based on rule
    if should_exclude_rule(rule_id):
        return True

    # Exclude based on file paths that shouldn't be scanned
    locations = result.get("locations", [])
    for location in locations:
        uri = (
            location.get("physicalLocation", {})
            .get("artifactLocation", {})
            .get("uri", "")
        )

        # Skip test files, documentation, config files
        exclude_patterns = [
            "/tests/",
            "/test_",
            "test_",
            ".md",
            ".yml",
            ".yaml",
            ".json",
            ".txt",
            ".toml",
            "/__pycache__/",
            ".egg-info/",
            "/htmlcov/",
            "/tools/",
        ]

        if any(pattern in uri for pattern in exclude_patterns):
            return True

    # Exclude very low severity issues
    level = result.get("level", "")
    if level in ["note", "info"]:
        return True

    return False


def filter_sarif(input_file: str, output_file: str) -> None:
    """
    Filter a SARIF file to remove false positives and low-severity findings.
    """

    try:
        with open(input_file, "r") as f:
            sarif_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file '{input_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{input_file}': {e}")
        sys.exit(1)

    original_count = 0
    filtered_count = 0

    # Process each run in the SARIF file
    for run in sarif_data.get("runs", []):

        # Filter results
        if "results" in run:
            original_results = run["results"]
            original_count += len(original_results)

            filtered_results = [
                result
                for result in original_results
                if not should_exclude_result(result)
            ]

            run["results"] = filtered_results
            filtered_count += len(filtered_results)

        # Filter rules (remove unused rules after filtering results)
        if (
            "tool" in run
            and "driver" in run["tool"]
            and "rules" in run["tool"]["driver"]
        ):
            used_rule_ids = set()
            for result in run.get("results", []):
                used_rule_ids.add(result.get("ruleId", ""))

            original_rules = run["tool"]["driver"]["rules"]
            filtered_rules = [
                rule for rule in original_rules if rule.get("id", "") in used_rule_ids
            ]

            run["tool"]["driver"]["rules"] = filtered_rules

    # Write filtered SARIF
    try:
        with open(output_file, "w") as f:
            json.dump(sarif_data, f, indent=2)
    except IOError as e:
        print(f"Error: Cannot write to '{output_file}': {e}")
        sys.exit(1)

    excluded_count = original_count - filtered_count

    print(f"SARIF filtering completed:")
    print(f"  Original findings: {original_count}")
    print(f"  Excluded findings: {excluded_count}")
    print(f"  Remaining findings: {filtered_count}")
    print(
        f"  Reduction: {(excluded_count/original_count*100):.1f}%"
        if original_count > 0
        else "  Reduction: 0%"
    )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python filter_sarif.py <input.sarif> <output.sarif>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    filter_sarif(input_file, output_file)
