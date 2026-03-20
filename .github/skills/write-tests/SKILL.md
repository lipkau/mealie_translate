---
name: write-tests
description: Patterns and workflow for writing tests in this project. USE FOR: adding unit tests for new code; understanding how to mock dependencies; knowing which test file to add tests to; running tests locally. DO NOT USE FOR: running the application; deployment; documentation style.
argument-hint: "[module or feature to test]"
---

# Writing Tests

Tests live in `tests/` and use `pytest`.
There are two categories: **unit** (fast, no external calls) and **integration** (real API calls).

## Running Tests

```bash
make test-unit          # Unit tests only — run these frequently during development
make test-integration   # Integration tests — requires API keys in .env
make test               # All tests
make test-coverage      # Tests + HTML/XML coverage reports in htmlcov/
```

## Test File Naming

| Test target | Test file |
| --- | --- |
| `mealie_translate/translator.py` | `tests/test_translator.py` |
| `mealie_translate/mealie_client.py` | `tests/test_mealie_client.py` |
| `mealie_translate/config.py` | `tests/test_config.py` |

Follow the `test_<module>.py` naming convention.

## Unit Test Pattern

Unit tests mock all external dependencies (HTTP, OpenAI API, file I/O).

```python
"""Tests for MyModule."""

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from mealie_translate.my_module import MyClass
from mealie_translate.config import Settings


@pytest.fixture
def mock_settings():
    return Settings(
        mealie_base_url="https://test.mealie.com",
        mealie_api_token="test_token",
        openai_api_key="test_key",
    )


def test_my_class_initialization(mock_settings):
    obj = MyClass(mock_settings)
    assert obj.some_attribute == "expected_value"
```

## Mocking HTTP Calls

Use the `responses` library to mock HTTP calls (already in dev dependencies):

```python
import responses

@responses.activate
def test_api_call(mealie_client):
    responses.add(
        responses.GET,
        "https://test.mealie.com/api/recipes",
        json={"items": []},
        status=200,
    )
    result = mealie_client.get_recipes()
    assert result == []
```

## Mocking with `unittest.mock`

```python
from unittest.mock import Mock, patch

def test_with_patch():
    with patch("mealie_translate.translator.openai.OpenAI") as mock_openai:
        mock_openai.return_value.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content="translated text"))]
        )
        # ... test code
```

## What to Test

- Happy path: normal inputs produce expected outputs.
- Edge cases: empty inputs, boundary values.
- Error handling: API failures, invalid responses.
- Do **not** write tests that verify mock behaviour — test real logic.

## Code Quality for Tests

Run the same linting on tests as on production code:

```bash
make lint       # Includes tests/
make format     # Auto-formats tests/ too
```

Type hints are required for public functions in production code; they are encouraged but not enforced in tests.
