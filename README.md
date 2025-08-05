# Mealie Recipe Translator

[![CI](https://github.com/lipkau/mealie_translate/actions/workflows/ci.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/ci.yml)
[![CD](https://github.com/lipkau/mealie_translate/actions/workflows/cd.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/cd.yml)
[![Security](https://github.com/lipkau/mealie_translate/actions/workflows/security.yml/badge.svg)](https://github.com/lipkau/mealie_translate/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-available-blue.svg)](https://github.com/lipkau/mealie_translate/pkgs/container/mealie_translate)

A Python application that translates Mealie recipes using the OpenAI ChatGPT API and converts imperial units to metric.

📚 **[Complete Documentation](docs/)** - Deployment guides, development tools, and advanced configuration

## Requirements

- **Python**: 3.11+ (Recommended: 3.13.0)
- **Node.js**: 18+ (for documentation linting with markdownlint)
- **APIs**: OpenAI API key, Mealie server access

### Python Version Management

This project uses specific Python version requirements for consistency:

- **Minimum**: Python 3.11
- **Recommended**: Python 3.13.0 (specified in `.python-version`)

**Using pyenv (recommended)**:

```bash
# Install pyenv first: https://github.com/pyenv/pyenv#installation
pyenv install 3.13.0
pyenv local 3.13.0  # This reads .python-version file
```

**Check your Python version**:

```bash
make check-python  # Validates version compatibility
```

## Features

- **Recipe Translation**: Translates recipe titles, descriptions, instructions, and ingredients
- **Unit Conversion**: Automatically converts imperial units (cups, pounds, °F) to metric (ml, grams, °C)
- **Batch Processing**: Efficiently processes multiple recipes
- **Smart Tracking**: Uses recipe extras field to prevent duplicate processing
- **Error Handling**: Robust retry logic with exponential backoff
- **Model Flexibility**: Configurable GPT model selection

## Installation

### Option 1: Quick Setup with Make (Recommended)

The easiest way to set up the project:

```bash
git clone <repository-url>
cd mealie_translate

# Quick setup: creates venv, installs dependencies, sets up env config
make setup

# OR for contributors: includes optional pre-commit hooks (recommended)
make setup-full

# Install Node.js dependencies for documentation linting
npm install

# Edit .env with your API keys and settings (see .env.example for details)
```

This will:

- Create a virtual environment
- Install all Python development dependencies
- Install Node.js dependencies for documentation linting
- Copy .env.example to .env (if .env doesn't exist)
- Set up pre-commit hooks for code quality
- Get you ready to develop immediately

### Option 2: Manual Setup

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd mealie_translate
   ```

2. Create and activate virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -e .
   ```

   For development with testing tools:

   ```bash
   pip install -e .[dev]
   ```

4. Install Node.js dependencies (for documentation linting):

   ```bash
   npm install
   ```

5. Configure environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings (see .env.example for details)
   ```

### Option 3: Docker (Production Ready)

For containerized deployment:

```bash
git clone <repository-url>
cd mealie_translate

# Setup environment
make setup-env  # Creates .env from template
# Edit .env with your API keys

# Build and run with Docker
make docker-build
make docker-run

# Or use development mode with live code reloading
make docker-dev

# Alternative: Use pre-built images from GitHub Container Registry
docker pull ghcr.io/lipkau/mealie_translate:latest
```

See [Docker Documentation](docs/DOCKER.md) for detailed Docker deployment guide.

## Configuration

Copy `.env.example` to `.env` and configure your settings:

```bash
cp .env.example .env
```

Then edit `.env` with your API keys and preferences.
See `.env.example` for all available configuration options and their descriptions.

## Usage

### Basic Usage

Run the main application:

```bash
# With Make (recommended)
make run

# Or directly with Python
python main.py
```

### Development Commands

The project provides comprehensive Make commands for development workflow. Run `make help` for all available commands.

#### Essential Commands

```bash
# Testing
make test           # Run all tests
make test-unit      # Unit tests only (fast)
make test-coverage  # Tests with coverage report

# Code Quality
make lint           # Check code quality (ruff, pyright)
make format         # Auto-format code (ruff)
make security-scan  # Security checks (bandit, pip-audit)

# Utilities
make clean          # Remove cache files
make run            # Start the application
make help           # Show all commands
```

#### Git Hooks (Optional)

Pre-commit hooks automatically maintain code quality:

```bash
make pre-commit           # Install hooks (interactive)
make pre-commit-uninstall # Remove hooks
```

Hooks run on every commit to:

- Format code (ruff)
- Check linting (ruff, pyright)
- Run unit tests
- Fix common issues

#### Advanced Development

```bash
# Model Comparison Tools
make compare-models       # Detailed model performance analysis
make verify-prompts       # Verify prompt consistency

# Docker Development
make docker-build         # Build Docker image
make docker-dev          # Run in containerized environment
make docker-test         # Run tests in Docker

# Integration Testing (requires API keys)
make test-integration    # Test with real Mealie/OpenAI APIs
```

### Using as a Module

```python
from mealie_translate.config import get_settings
from mealie_translate.recipe_processor import RecipeProcessor

settings = get_settings()
processor = RecipeProcessor(settings)
processor.process_all_recipes()
```

## Unit Conversions

The application automatically converts imperial units to metric:

### Volume Conversions

- 1 cup = 240 ml
- 1 tablespoon = 15 ml
- 1 teaspoon = 5 ml
- 1 fluid ounce = 30 ml
- 1 pint = 473 ml
- 1 quart = 946 ml
- 1 gallon = 3785 ml

### Mass Conversions

- 1 pound = 454 g
- 1 ounce = 28 g
- 1 stone = 6350 g

### Temperature Conversions

- °F to °C: (°F - 32) × 5/9

## Development Tools

The project includes development tools in the `tools/` directory:

- **Basic Model Comparison**: `tools/basic_model_comparison.py` - Quick comparison of different GPT models
- **Detailed Model Comparison**: `tools/detailed_model_comparison.py` - Comprehensive model analysis with full output details
- **Prompt Verification**: `tools/verify_prompt_consistency.py` - Ensures model comparisons use production prompts
- See `tools/README.md` for detailed documentation

## Testing

Run the test suite:

```bash
# With Make (recommended)
make test           # All tests
make test-unit      # Unit tests only
make test-integration  # Integration tests only
make test-coverage  # Tests with coverage report

# Or directly with pytest
pytest tests/
pytest tests/ --cov=mealie_translate
```

## Development Workflow

This project supports two development approaches:

### Quick Start with Make (Recommended)

1. **Setup**: `make setup` - Creates venv and installs dependencies
   - Or `make setup-full` - Includes optional pre-commit hooks (for contributors)
2. **Environment**: `make setup-env` - Copies .env template (then edit with your API keys)
3. **Test**: `make test` - Runs all tests
4. **Lint**: `make lint` - Code quality checks
5. **Format**: `make format` - Auto-format code
6. **Run**: `make run` - Execute the application
7. **Help**: `make help` - See all available commands

### Manual Development

If you prefer manual control:

1. Create your own virtual environment (any name: `venv`, `.venv`, `env`)
2. Install with `pip install -e .[dev]`
3. Use standard Python/pytest commands

The project auto-detects your virtual environment location.

## Project Structure

```text
mealie_translate/
├── .github/                  # GitHub configuration
│   ├── workflows/           # CI/CD pipelines
│   │   ├── ci.yml          # Continuous Integration
│   │   ├── cd.yml          # Continuous Deployment
│   │   ├── security.yml    # Security scanning
│   │   └── dependabot.yml  # Dependency updates
│   ├── ISSUE_TEMPLATE/     # Issue templates
│   ├── CODE_OF_CONDUCT.md
│   ├── CONTRIBUTING.md
│   ├── SECURITY.md
│   └── copilot-instructions.md
├── .vscode/                 # VS Code configuration
│   ├── settings.json
│   └── extensions.json
├── docs/                    # Comprehensive documentation
│   ├── README.md           # Documentation index
│   ├── DEVELOPMENT.md      # Developer guide
│   ├── DOCKER.md          # Docker deployment
│   ├── CI_CD_ARCHITECTURE.md
│   ├── SECURITY_ARCHITECTURE.md
│   └── ...
├── mealie_translate/        # Main package
│   ├── __init__.py
│   ├── config.py           # Configuration management
│   ├── logger.py           # Logging utilities
│   ├── main.py            # Application entry point
│   ├── mealie_client.py   # Mealie API client
│   ├── translator.py      # OpenAI translation service
│   └── recipe_processor.py # Main processing logic
├── tests/                   # Comprehensive test suite
│   ├── test_config.py
│   ├── test_logger.py
│   ├── test_main.py
│   ├── test_mealie_client.py
│   ├── test_translator.py
│   ├── test_recipe_processor.py
│   ├── test_integration.py
│   └── test_comprehensive.py
├── tools/                   # Development and analysis tools
│   ├── README.md
│   ├── basic_model_comparison.py
│   ├── detailed_model_comparison.py
│   └── verify_prompt_consistency.py
├── scripts/                 # Deployment scripts
│   └── docker-entrypoint.sh
├── .env.example            # Environment template
├── .python-version         # Python version specification
├── .pre-commit-config.yaml # Pre-commit hooks configuration
├── docker-compose.yml      # Docker orchestration
├── Dockerfile             # Multi-stage Docker build
├── LICENSE                # MIT license
├── Makefile              # Development automation (35+ commands)
├── pyproject.toml        # Project configuration
├── README.md             # Main documentation
└── main.py              # Application entry point
```

## API Integration

### Mealie API

- Fetches recipes via GET `/api/recipes`
- Updates recipes via PUT `/api/recipes/{id}`
- Uses Bearer token authentication
- Tracks processing via recipe extras field

### OpenAI API

- Uses ChatGPT for translation and unit conversion
- Configurable model selection (default: gpt-4o-mini)
- Retry logic with exponential backoff
- Optimized prompts for accuracy

## Processing Logic

1. **Fetch Recipes**: Retrieves all recipes from Mealie API
2. **Filter Processed**: Skips recipes already marked as translated
3. **Translate Content**: Processes title, description, instructions, and ingredients
4. **Convert Units**: Applies imperial-to-metric conversions
5. **Update Recipe**: Saves translated content back to Mealie
6. **Mark Complete**: Sets `extras.translated = "true"` to prevent reprocessing

## Error Handling

- **API Rate Limits**: Exponential backoff retry strategy
- **Network Issues**: Configurable retry attempts
- **Translation Failures**: Graceful degradation with error logging
- **Invalid Responses**: Input validation and fallback handling

## Contributing

We welcome contributions! Here's how to get started:

### Quick Start for Contributors

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/mealie_translate.git
cd mealie_translate

# 2. Set up development environment
make setup-full  # Includes git hooks for code quality

# 3. Create feature branch
git checkout -b feature/your-feature

# 4. Development cycle
make test-unit   # Quick tests while developing
make format      # Format your code
make lint        # Check code quality
make test        # Full test suite

# 5. Submit pull request
```

### Key Commands for Contributors

Run `make help` to see all available commands. Key commands for contributors:

```bash
make setup-full     # Complete development setup
make test          # Run all tests
make lint          # Check code quality
make format        # Auto-format code
make security-scan # Security checks
```

### Detailed Guidelines

See our comprehensive development documentation:

- **[Development Guide](docs/DEVELOPMENT.md)** - Complete Makefile commands reference and workflows
- **[CONTRIBUTING.md](.github/CONTRIBUTING.md)** - Contribution guidelines and setup instructions
