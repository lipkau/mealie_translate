# Development Guide

Complete guide for developers working on the Mealie Recipe Translator project.

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/lipkau/mealie_translate.git
cd mealie_translate
make setup-full  # Complete contributor setup
npm install      # Node.js dependencies for documentation linting

# 2. Verify installation
make test-unit   # Quick verification
make help        # See all available commands
```

## Makefile Commands Reference

The project uses Make for all development tasks. Run `make help` for the latest list.

### Setup Commands

| Command             | Description                                   | When to Use                |
| ------------------- | --------------------------------------------- | -------------------------- |
| `make setup`        | Basic setup: venv + dependencies + env config | First-time setup, users    |
| `make setup-full`   | Complete setup + optional git hooks           | Contributors, maintainers  |
| `make setup-env`    | Copy .env.example to .env                     | After setup, configuration |
| `make check-python` | Verify Python version compatibility           | Troubleshooting            |

### Testing Commands

| Command                 | Description                                           | When to Use               |
| ----------------------- | ----------------------------------------------------- | ------------------------- |
| `make test`             | Run all tests (unit + integration) + generate reports | Before committing         |
| `make test-unit`        | Run unit tests only + generate reports                | During development (fast) |
| `make test-integration` | Run integration tests + generate reports              | With API keys configured  |
| `make test-coverage`    | Run tests with coverage + all reports                 | Coverage analysis         |

> **Note:** All test commands now generate JUnit XML and HTML reports for better debugging

### Code Quality Commands

| Command                 | Description                  | When to Use         |
| ----------------------- | ---------------------------- | ------------------- |
| `make lint`             | Run linting (ruff, pyright)  | Check code quality  |
| `make lint-format`      | Check code formatting only   | Verify formatting   |
| `make lint-markdown`    | Check markdown formatting    | Verify docs         |
| `make lint-all`         | Run all linting checks       | Comprehensive check |
| `make lint-no-markdown` | Run linting without markdown | CI environments     |
| `make format`           | Auto-format code (ruff)      | Before committing   |

> **Note:** `lint-markdown` uses Node.js dependencies from `package.json`. Run `npm install` first if needed.
> **CI Note:** Use `lint-no-markdown` in CI environments without Node.js setup.

### Security Commands

| Command                   | Description                           | When to Use         |
| ------------------------- | ------------------------------------- | ------------------- |
| `make security-scan`      | Run all security scans                | Before releases     |
| `make security-bandit`    | Run bandit static analysis            | Security review     |
| `make security-pip-audit` | Scan dependencies for vulnerabilities | Dependency security |

### Git Hooks Commands

| Command                     | Description                     | When to Use            |
| --------------------------- | ------------------------------- | ---------------------- |
| `make pre-commit`           | Install git hooks (interactive) | Setup for contributors |
| `make pre-commit-force`     | Install git hooks (automation)  | CI/CD pipelines        |
| `make pre-commit-uninstall` | Remove git hooks                | Disable automation     |

### Development Tools

| Command                     | Description               | When to Use        |
| --------------------------- | ------------------------- | ------------------ |
| `make compare-models`       | Detailed model comparison | Model evaluation   |
| `make compare-models-basic` | Basic model comparison    | Quick evaluation   |
| `make verify-prompts`       | Verify prompt consistency | Prompt development |

### Docker Commands

| Command             | Description                 | When to Use               |
| ------------------- | --------------------------- | ------------------------- |
| `make docker-build` | Build Docker image          | Local Docker testing      |
| `make docker-run`   | Run with cron scheduling    | Production simulation     |
| `make docker-dev`   | Run development environment | Containerized development |
| `make docker-logs`  | Follow container logs       | Debugging                 |
| `make docker-test`  | Run tests in Docker         | Environment testing       |
| `make docker-clean` | Clean Docker artifacts      | Cleanup                   |

### Utility Commands

| Command          | Description                              | When to Use                |
| ---------------- | ---------------------------------------- | -------------------------- |
| `make run`       | Run the main application                 | Testing functionality      |
| `make clean`     | Clean up cache files and reports         | Cleanup, troubleshooting   |
| `make clean-all` | Deep clean including virtual environment | Fresh start, major cleanup |
| `make help`      | Show all available commands              | Reference                  |

## Development Workflow

### 1. Initial Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/mealie_translate.git
cd mealie_translate

# Complete setup for contributors
make setup-full
# This will:
# - Create virtual environment
# - Install all dependencies (production + development)
# - Copy .env.example to .env
# - Optionally install git hooks

# Configure your environment
# Edit .env with your API keys (for integration tests)
```

### 2. Feature Development

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Development cycle
make test-unit          # Quick tests (no API calls)
# ... make your changes ...
make format             # Auto-format your code
make lint               # Check code quality
make test-unit          # Verify tests still pass

# Before committing
make test               # Full test suite
make security-scan      # Security checks (optional)
```

### 3. Pre-commit Hooks (Optional but Recommended)

If you installed git hooks with `make setup-full` or `make pre-commit`, they will automatically run on every commit:

- Code formatting and linting (ruff)
- Unit tests
- Common issue fixes

### 4. Testing Strategy

#### Unit Tests (Fast - No External Dependencies)

```bash
make test-unit
# - Mocked external APIs
# - Fast execution (~10-30 seconds)
# - Run frequently during development
```

#### Integration Tests (Slow - Requires API Keys)

```bash
make test-integration
# - Real API calls to OpenAI and Mealie
# - Requires valid .env configuration
# - Run before major commits/releases
```

#### Coverage Analysis

```bash
make test-coverage
# - Generates HTML coverage report in htmlcov/
# - Generates XML coverage report for CI/tools
# - Generates JUnit XML test results
# - Generates HTML test report for browser viewing
# - Shows line-by-line coverage
# - Helps identify untested code
```

**Generated Test Reports:**

- `pytest-results-coverage.xml` - JUnit test results
- `pytest-report-coverage.html` - Interactive HTML test report
- `coverage.xml` - Coverage data for CI tools
- `htmlcov/` - Detailed HTML coverage report

### 5. Code Quality Standards

#### Formatting

- **Ruff**: Fast linter and formatter (replaces black, flake8, isort)
- **editorconfig**: Consistent editor settings

#### Linting and Static Analysis

- **Ruff**: Fast linter and formatter (replaces black, flake8, isort) - Modern Rust-based tool
  - **Performance**: ~10-100x faster than the tools it replaces
  - **Features**: Unified linting and formatting
- **Pyright**: Static type checking (via Node.js)
  - **Integration**: Native VS Code support through Pylance
  - **Performance**: Faster than mypy
- **Bandit**: Security issue detection

#### Security

- **bandit**: Static analysis for security issues
- **pip-audit**: Dependency vulnerability scanning
- **Trivy**: Container image scanning (in CI)

## Project Structure

```text
mealie_translate/
├── mealie_translate/          # Main package
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── logger.py             # Logging setup
│   ├── main.py               # CLI entry point
│   ├── mealie_client.py      # Mealie API client
│   ├── recipe_processor.py   # Main processing logic
│   └── translator.py         # OpenAI translation client
├── tests/                     # Test suite
│   ├── test_*.py             # Unit tests
│   └── test_integration.py   # Integration tests
├── tools/                     # Development tools
│   ├── basic_model_comparison.py
│   ├── detailed_model_comparison.py
│   └── verify_prompt_consistency.py
├── docs/                      # Documentation
├── .github/                   # GitHub workflows and templates
├── Dockerfile                 # Container definition
├── pyproject.toml            # Project metadata and dependencies
├── Makefile                  # Development commands
└── main.py                   # Application entry point
```

## Environment Configuration

### Required Environment Variables

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
OPENAI_MAX_TOKENS=4000
OPENAI_TEMPERATURE=0.1

# Mealie Configuration
MEALIE_BASE_URL=http://your-mealie-server
MEALIE_API_TOKEN=your_mealie_token

# Application Configuration
TARGET_LANGUAGE=German
LOG_LEVEL=INFO
MAX_RETRIES=3
DELAY_BETWEEN_REQUESTS=1.0
```

### Development vs Production

- **Testing**: Integration tests require real API keys
- **Production**: Use environment-specific configuration

## Troubleshooting

### Common Issues

#### Python Version

```bash
make check-python  # Verify Python 3.11+ is available
```

#### Virtual Environment Issues

```bash
# Clean slate setup
rm -rf .venv
make setup
```

#### Test Failures

```bash
# Check specific test output
make test-unit -v

# Run specific test file
.venv/bin/python -m pytest tests/test_specific.py -v
```

#### Docker Issues

```bash
# Clean Docker state
make docker-clean

# Rebuild from scratch
make docker-build
```

### Getting Help

1. **Check Documentation**: README.md, docs/, tools/README.md
2. **Run Tests**: Verify your environment with `make test-unit`
3. **Check Issues**: GitHub issues for known problems
4. **Ask Questions**: Create a GitHub discussion

## Release Process

### Version Management

1. **Update Version**: Edit `pyproject.toml`
2. **Create Tag**: `git tag v1.0.0`
3. **Push**: `git push origin main && git push origin v1.0.0`
4. **Automatic**: GitHub Actions builds and publishes Docker images

### Docker Images

Published to GitHub Container Registry (GHCR):

- `ghcr.io/lipkau/mealie_translate:latest` (production)
- `ghcr.io/lipkau/mealie_translate:dev` (development)
- `ghcr.io/lipkau/mealie_translate:v1.0.0` (version tags)

## Best Practices

### Code Organization

- **Single Responsibility**: Each module has a clear purpose
- **Dependency Injection**: Use settings/config for external dependencies
- **Error Handling**: Comprehensive error handling with retries
- **Logging**: Structured logging for debugging and monitoring

### Testing

- **Unit Tests**: Fast, isolated, mocked external dependencies
- **Integration Tests**: Real API calls, slower, require configuration
- **Coverage**: Aim for >90% code coverage
- **Fixtures**: Reusable test data and mocks

### Security

- **API Keys**: Never commit credentials
- **Dependencies**: Regular security scanning
- **Input Validation**: Validate all external inputs
- **Least Privilege**: Minimal required permissions

### Documentation

- **Code Comments**: Explain why, not what
- **Docstrings**: All public functions and classes
- **README**: Keep user documentation up to date
- **CHANGELOG**: Document breaking changes and new features

## Contributing Guidelines

1. **Fork** the repository
2. **Create** a feature branch
3. **Follow** the development workflow above
4. **Test** your changes thoroughly
5. **Document** new features
6. **Submit** a pull request

See [CONTRIBUTING.md](../.github/CONTRIBUTING.md) for detailed guidelines.

## Development Tools

This project includes specialized tools for model comparison and development testing.

### Model Comparison Tools

Both model comparison tools **directly call methods** from the production `RecipeTranslator` class to ensure perfect consistency.
Any improvements to the prompts or logic automatically apply to both production and testing.

#### Detailed Model Comparison

A comprehensive tool for comparing different GPT models for recipe translation and unit conversion accuracy.

**Features:**

- Tests multiple GPT models side-by-side
- Evaluates unit conversion accuracy
- Measures response time and success rates
- Provides detailed analysis and recommendations
- Easily configurable for new models (GPT-4.1 series when available)

**Usage:**

```bash
# Run comprehensive model comparison
make compare-models

# Or run directly
python tools/detailed_model_comparison.py
```

#### Basic Model Comparison

A simpler model comparison tool for quick testing and basic performance metrics.

**Features:**

- Quick model performance comparison
- Basic success/failure metrics
- Lightweight testing framework
- Good for development and debugging

**Usage:**

```bash
# Run basic model comparison
make compare-models-basic

# Or run directly
python tools/basic_model_comparison.py
```

#### Prompt Consistency Verification

Ensures that model comparison tools use the same prompts as production code.

**Usage:**

```bash
# Verify prompt consistency
make verify-prompts

# Or run directly
python tools/verify_prompt_consistency.py
```

### Development Utilities

- **Model comparison scripts** in `tools/` directory
- **Test data generation** for unit and integration tests
- **Performance benchmarking** tools
- **API response validation** utilities

## Implementation Optimizations

This section documents the ChatGPT and Mealie API optimizations implemented to improve the recipe translation process.

### REST API Optimizations

#### Smart Recipe Filtering

**Enhancement**: Added `exclude_tag` parameter to `get_all_recipes()` method to filter out already processed recipes at
the API level.

**Before**: Fetched all recipes, then filtered locally for processed recipes.

**After**: Filter at API level to reduce unnecessary calls.

**Benefit**: Reduces unnecessary API calls and improves performance.

```python
# New method signature
def get_all_recipes(self, exclude_tag: Optional[str] = None) -> List[Dict[str, Any]]:
```

#### Enhanced Error Handling

**Enhancement**: Graceful handling of 404 responses for missing recipes.

**Before**: Basic error handling that raised exceptions for 404s.

**After**: Returns `None` for missing recipes, cleaner error flow.

**Benefit**: More robust error handling, cleaner code flow.

#### Data Sanitization

**Enhancement**: Automatically removes read-only fields before API updates.

**Before**: Sent complete recipe data including read-only fields.

**After**: Automatically removes fields that could cause API errors.

**Benefit**: Prevents API errors from attempting to update read-only fields.

```python
# Automatically removed fields
read_only_fields = ['id', 'userId', 'householdId', 'groupId', 'createdAt', 'updatedAt', 'dateAdded', 'dateUpdated']
```

### Recipe Processing Optimizations

#### Smart Recipe Tracking

**Enhancement**: Uses the `extras` field to mark processed recipes with `"translated": "true"`.

**Before**: Used tags to mark processed recipes, which could interfere with Mealie's UI functionality.

**After**: Uses the `extras` field for cleaner implementation.

**Benefit**: Doesn't affect recipe tagging, more reliable tracking.

```python
# Recipe marked as processed in extras field
recipe['extras'] = {'translated': 'true'}
```

#### Batch Processing Efficiency

**Enhancement**: Intelligent batching and error recovery.

**Before**: Sequential processing with limited error handling.

**After**: Optimized batching with retry logic and progress tracking.

**Benefit**: Better performance and reliability for large recipe collections.

### OpenAI API Optimizations

#### Prompt Engineering

**Enhancement**: Optimized prompts for better translation accuracy and consistency.

**Key Improvements:**

- Structured prompts for unit conversion
- Context-aware translation instructions
- Consistent formatting requirements
- Error reduction techniques

#### Model Selection Strategy

**Enhancement**: Configurable model selection with fallback options.

**Features:**

- Primary model configuration (GPT-4, GPT-3.5-turbo)
- Automatic fallback for rate limiting
- Cost optimization for different use cases
- Performance monitoring and comparison

#### Response Parsing

**Enhancement**: Robust JSON parsing with error recovery.

**Before**: Basic JSON parsing that failed on malformed responses.

**After**: Multiple parsing strategies with fallback options.

**Benefit**: Better handling of edge cases and API response variations.

### Performance Monitoring

#### Metrics Collection

- **Translation accuracy** tracking
- **API response times** monitoring
- **Error rate** analysis
- **Cost optimization** metrics

#### Logging and Debugging

- **Structured logging** for better debugging
- **Request/response tracking** for API calls
- **Performance profiling** for optimization
- **Error categorization** for issue resolution
