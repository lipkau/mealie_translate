# =============================================================================
# Mealie Recipe Translator - Makefile
# =============================================================================
# Primary development interface. Run `make help` for available commands.
# =============================================================================

# -----------------------------------------------------------------------------
# .PHONY declarations (organized by category)
# -----------------------------------------------------------------------------

# Setup targets
.PHONY: help setup setup-full setup-env install install-dev check-python

# Test targets
.PHONY: test test-unit test-integration test-coverage

# Lint & format targets
.PHONY: lint lint-format lint-markdown lint-all lint-no-markdown format check

# CI targets (use system Python, no HTML reports)
.PHONY: ci-lint ci-test-unit ci-test-coverage ci-test-integration

# Pre-commit targets
.PHONY: pre-commit pre-commit-force pre-commit-uninstall pre-commit-lint pre-commit-format pre-commit-test

# Cleanup targets
.PHONY: clean clean-all clean-force

# Application targets
.PHONY: run compare-models compare-models-basic verify-prompts generate-tags

# Docker targets
.PHONY: docker-build docker-run docker-dev docker-logs docker-test docker-clean

# Security targets
.PHONY: security-scan security-bandit security-pip-audit

# Internal prerequisite targets (not for direct use)
.PHONY: .ensure-python .ensure-pytest .ensure-ruff .ensure-precommit

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Source directories for linting/formatting
SOURCES := mealie_translate/ tests/ tools/ main.py

# Auto-detect virtual environment or use default
VENV_PATH := $(shell if [ -d ".venv" ]; then echo ".venv"; elif [ -d "venv" ]; then echo "venv"; elif [ -d "env" ]; then echo "env"; elif [ -n "$(VIRTUAL_ENV)" ]; then echo "$(VIRTUAL_ENV)"; else echo ".venv"; fi)
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip

# Python version requirements
REQUIRED_PYTHON_VERSION := 3.11
PREFERRED_PYTHON_VERSION := 3.14.0

# Check if pyenv is available and .python-version exists
PYENV_AVAILABLE := $(shell command -v pyenv 2> /dev/null)
PYTHON_VERSION_FILE := $(shell if [ -f ".python-version" ]; then echo ".python-version"; fi)

# Determine which Python to use for venv creation
ifeq ($(PYENV_AVAILABLE),)
    # No pyenv, use system python3
    PYTHON_FOR_VENV := python3
else
    ifneq ($(PYTHON_VERSION_FILE),)
        # pyenv available and .python-version exists
        PYTHON_FOR_VENV := $(shell pyenv which python 2>/dev/null || echo python3)
    else
        # pyenv available but no .python-version
        PYTHON_FOR_VENV := python3
    endif
endif

# -----------------------------------------------------------------------------
# Prerequisite checks (DRY pattern for dependency validation)
# -----------------------------------------------------------------------------

.ensure-python:
	@$(PYTHON) --version >/dev/null 2>&1 || { echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; exit 1; }

.ensure-pytest: .ensure-python
	@$(PYTHON) -c "import pytest" 2>/dev/null || { echo "⚠️  pytest not found. Run 'make setup' first."; exit 1; }

.ensure-ruff: .ensure-python
	@$(PYTHON) -c "import ruff" 2>/dev/null || { echo "⚠️  ruff not found. Run 'make setup' first."; exit 1; }

.ensure-precommit:
	@$(VENV_PATH)/bin/pre-commit --version >/dev/null 2>&1 || { echo "⚠️  pre-commit not found. Run 'make setup' first."; exit 1; }

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------

help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup                Create virtual environment and install dependencies"
	@echo "  setup-full           Complete setup including pre-commit hooks (recommended for contributors)"
	@echo "  setup-env            Copy .env.example to .env (run after setup, or included in setup)"
	@echo "  install              Install production dependencies"
	@echo "  install-dev          Install development dependencies"
	@echo "  check-python         Check Python version compatibility"
	@echo ""
	@echo "Testing:"
	@echo "  test                 Run all tests (generates JUnit XML and HTML reports)"
	@echo "  test-unit            Run unit tests only (generates JUnit XML and HTML reports)"
	@echo "  test-integration     Run integration tests (generates JUnit XML and HTML reports)"
	@echo "  test-coverage        Run tests with coverage report (generates JUnit XML, HTML, and coverage reports)"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint                 Run code linting (ruff, pyright)"
	@echo "  lint-format          Check code formatting (ruff)"
	@echo "  lint-markdown        Check markdown formatting (markdownlint-cli2)"
	@echo "  lint-all             Run all linting and formatting checks"
	@echo "  lint-no-markdown     Run linting without markdown (for CI)"
	@echo "  format               Format code with ruff"
	@echo "  check                Test local changes: lint-all + test (⭐ shorthand)"
	@echo ""
	@echo "CI Targets (use system Python, minimal output):"
	@echo "  ci-lint              Run linting for CI (no venv, includes pyright)"
	@echo "  ci-test-unit         Run unit tests for CI (JUnit XML only)"
	@echo "  ci-test-coverage     Run tests with coverage for CI (XML reports only)"
	@echo "  ci-test-integration  Run integration tests for CI (JUnit XML only)"
	@echo ""
	@echo "Security:"
	@echo "  security-scan        Run all security scans (bandit + pip-audit)"
	@echo "  security-bandit      Run bandit security scanner (creates bandit-report.json)"
	@echo "  security-pip-audit   Run pip-audit dependency vulnerability scanner (creates pip-audit-report.json)"
	@echo ""
	@echo "Pre-commit Hooks:"
	@echo "  pre-commit           Install git hooks (interactive, with detailed warnings)"
	@echo "  pre-commit-force     Install git hooks without prompting (for automation)"
	@echo "  pre-commit-uninstall Remove git hooks from repository"
	@echo "  pre-commit-lint      Lightweight lint for pre-commit (no output)"
	@echo "  pre-commit-format    Lightweight format for pre-commit (no output)"
	@echo "  pre-commit-test      Lightweight test for pre-commit (quiet mode)"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean                Clean up cache files, test reports, and build artifacts"
	@echo "  clean-all            Deep clean including virtual environment (interactive)"
	@echo "  clean-force          Deep clean without prompting (for automation)"
	@echo ""
	@echo "Application:"
	@echo "  run                  Run the main application"
	@echo "  compare-models       Run detailed model comparison"
	@echo "  compare-models-basic Run basic model comparison"
	@echo "  verify-prompts       Verify model comparison uses production prompts"
	@echo "  generate-tags        Generate and assign tags for all recipes using LLM"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build         Build Docker image"
	@echo "  docker-run           Run application in Docker container with cron scheduling"
	@echo "  docker-dev           Run development environment (single run)"
	@echo "  docker-logs          Follow Docker container logs"
	@echo "  docker-test          Run tests in Docker container"
	@echo "  docker-clean         Clean Docker images and containers"
	@echo ""
	@echo "Environment Info:"
	@echo "  Virtual environment: $(VENV_PATH)"
ifneq ($(PYENV_AVAILABLE),)
	@echo "  Pyenv: Available"
ifneq ($(PYTHON_VERSION_FILE),)
	@echo "  Python version file: $(shell cat .python-version)"
endif
else
	@echo "  Pyenv: Not available"
endif
	@echo "  Python for venv: $(PYTHON_FOR_VENV)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup-full  # Complete setup for contributors"
	@echo "     OR"
	@echo "     make setup       # Basic setup (no npm deps or pre-commit hooks)"
	@echo "  2. Edit .env file with your API keys"
	@echo "  3. make run         # Start the application"

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

check-python:
	@echo "Checking Python version compatibility..."
	@python_version=$$($(PYTHON_FOR_VENV) -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"); \
	required_version="$(REQUIRED_PYTHON_VERSION)"; \
	echo "Detected Python version: $$python_version"; \
	echo "Required Python version: >=$$required_version"; \
	if [ "$$(printf '%s\n' "$$required_version" "$$python_version" | sort -V | head -n1)" = "$$required_version" ]; then \
		echo "✅ Python version $$python_version is compatible (>=$$required_version)"; \
	else \
		echo "❌ Python version $$python_version is too old. Please install Python $$required_version or newer."; \
		echo ""; \
		echo "Recommended installation methods:"; \
		echo "  • Using pyenv: pyenv install $(PREFERRED_PYTHON_VERSION) && pyenv local $(PREFERRED_PYTHON_VERSION)"; \
		echo "  • Using system package manager (brew, apt, etc.)"; \
		echo "  • Download from python.org"; \
		exit 1; \
	fi

setup: check-python
	@echo "Setting up development environment..."
	@if [ ! -d "$(VENV_PATH)" ]; then \
		echo "Creating virtual environment at $(VENV_PATH) using $(PYTHON_FOR_VENV)..."; \
		$(PYTHON_FOR_VENV) -m venv $(VENV_PATH); \
	else \
		echo "Virtual environment already exists at $(VENV_PATH)"; \
	fi
	@echo "Installing development dependencies..."
	$(PIP) install -e .[dev]
	@echo "Setting up environment configuration..."
	@$(MAKE) setup-env
	@echo "✅ Setup complete! Virtual environment ready at $(VENV_PATH)"
	@echo "📝 Please edit .env with your API keys and configuration"
	@echo ""
	@echo "💡 Tip: If you plan to contribute to this project, run 'make pre-commit' to install git hooks"

setup-full: setup
	@echo ""
	@echo "🔧 Installing Node.js dependencies for markdown linting..."
	@if command -v npm >/dev/null 2>&1; then \
		if [ -f "package.json" ]; then \
			npm install; \
			echo "✅ Node.js dependencies installed"; \
		else \
			echo "⚠️  package.json not found, skipping npm install"; \
		fi \
	else \
		echo "⚠️  npm not found. Please install Node.js to enable markdown linting."; \
		echo "💡 Download from: https://nodejs.org/ or use package manager (brew, apt, etc.)"; \
	fi
	@echo ""
	@echo "🔧 Final step: Git hooks for automatic code quality checks"
	@echo "⚠️  WARNING: This will modify your git repository behavior!"
	@echo ""
	@echo "What git hooks do:"
	@echo "  • Run automatically on every git commit"
	@echo "  • Block commits if code quality checks fail"
	@echo "  • Ensure consistent code formatting and testing"
	@echo "  • Remain active until manually removed"
	@echo ""
	@read -p "Install git hooks for this repository? (y/N): " answer; \
	if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
		$(VENV_PATH)/bin/pre-commit install; \
		echo "✅ Git hooks installed and active"; \
		echo "🔒 Commits will now be automatically checked"; \
	else \
		echo "⏭️  Git hooks skipped"; \
		echo "💡 Install later with: make pre-commit"; \
		echo "💡 Or run checks manually: make lint, make test"; \
	fi
	@echo "✅ Full setup complete!"

setup-env:
	@if [ ! -f ".env.example" ]; then \
		echo "⚠️  .env.example not found in current directory"; \
		exit 1; \
	fi
	@if [ -f ".env" ]; then \
		echo "⚠️  .env file already exists. Remove it first if you want to recreate it."; \
		echo "Current .env file preserved."; \
	else \
		cp .env.example .env; \
		echo "✅ Created .env file from .env.example"; \
		echo "📝 Please edit .env with your API keys and configuration"; \
	fi

install: .ensure-python
	$(PIP) install -e .

install-dev: .ensure-python
	$(PIP) install -e .[dev]

# -----------------------------------------------------------------------------
# Testing (local development - includes HTML reports)
# -----------------------------------------------------------------------------

test: .ensure-pytest
	$(PYTHON) -m pytest tests/ -v --junit-xml=pytest-results.xml --html=pytest-report.html --self-contained-html

test-unit: .ensure-pytest
	$(PYTHON) -m pytest tests/ -v -m "not integration" --junit-xml=pytest-results-unit.xml --html=pytest-report-unit.html --self-contained-html

test-integration: .ensure-pytest
	$(PYTHON) -m pytest tests/ -v -m "integration" --junit-xml=pytest-results-integration.xml --html=pytest-report-integration.html --self-contained-html

test-coverage: .ensure-pytest
	$(PYTHON) -m pytest tests/ --cov=mealie_translate --cov-report=html --cov-report=term --cov-report=xml --junit-xml=pytest-results-coverage.xml --html=pytest-report-coverage.html --self-contained-html

# -----------------------------------------------------------------------------
# CI Testing (system Python, no HTML reports, minimal overhead)
# -----------------------------------------------------------------------------

ci-test-unit:
	python -m pytest tests/ -v -m "not integration" --junit-xml=pytest-results.xml

ci-test-coverage:
	python -m pytest tests/ -v -m "not integration" --cov=mealie_translate --cov-report=xml --cov-report=term --junit-xml=pytest-results.xml

ci-test-integration:
	python -m pytest tests/ -v -m "integration" --junit-xml=pytest-results-integration.xml

# -----------------------------------------------------------------------------
# Linting & Formatting
# -----------------------------------------------------------------------------

lint: .ensure-ruff
	@echo "Running code linting..."
	$(PYTHON) -m ruff check $(SOURCES)
	@if ! command -v npx >/dev/null 2>&1; then \
		echo "⚠️  npx not found. Install Node.js or run 'npm install'."; \
		exit 1; \
	fi
	@if ! npx pyright --version >/dev/null 2>&1; then \
		echo "⚠️  pyright not found. Run 'npm install' to install dependencies."; \
		exit 1; \
	fi
	npx pyright

lint-format: .ensure-ruff
	@echo "Checking code formatting..."
	$(PYTHON) -m ruff format --check $(SOURCES)

lint-markdown:
	@echo "Checking markdown formatting..."
	@if command -v npx >/dev/null 2>&1 && [ -f package.json ]; then \
		echo "Using npm lint:markdown (from package.json)..."; \
		npm run lint:markdown; \
	else \
		echo "⚠️  markdownlint-cli2 not found. Install with: npm install"; \
		exit 1; \
	fi

lint-all: lint lint-format lint-markdown

lint-no-markdown: lint lint-format

format: .ensure-ruff
	@echo "Formatting code with ruff..."
	$(PYTHON) -m ruff check --fix $(SOURCES)
	$(PYTHON) -m ruff format $(SOURCES)

check: lint-all test

# -----------------------------------------------------------------------------
# CI Linting (system Python, no venv dependency checks)
# -----------------------------------------------------------------------------

ci-lint:
	@echo "Running CI linting..."
	python -m ruff check $(SOURCES)
	npx pyright

# -----------------------------------------------------------------------------
# Pre-commit Hooks
# -----------------------------------------------------------------------------

pre-commit: .ensure-precommit
	@echo "Installing pre-commit hooks..."
	@echo "⚠️  WARNING: This will modify your git repository behavior!"
	@echo ""
	@echo "What this does:"
	@echo "  • Creates executable scripts in .git/hooks/ directory"
	@echo "  • These hooks run automatically on EVERY git commit"
	@echo "  • Hooks will run: code formatting, linting, and unit tests"
	@echo "  • Failed checks will BLOCK your commit until fixed"
	@echo ""
	@echo "Persistence:"
	@echo "  • These hooks remain active until manually removed"
	@echo "  • To remove later: run 'pre-commit uninstall'"
	@echo "  • Files modified: .git/hooks/pre-commit (and others)"
	@echo ""
	@read -p "Do you want to install these git hooks? (y/N): " answer; \
	if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
		$(VENV_PATH)/bin/pre-commit install; \
		echo "✅ Pre-commit hooks installed successfully"; \
		echo "🔒 Git hooks are now active and will run on every commit"; \
		echo "💡 Test them with: pre-commit run --all-files"; \
		echo "🗑️  Remove them with: pre-commit uninstall"; \
	else \
		echo "⏭️  Pre-commit hooks installation cancelled"; \
		echo "💡 You can still run checks manually: make lint, make test, make format"; \
	fi

pre-commit-force: .ensure-precommit
	@echo "Installing pre-commit hooks (non-interactive)..."
	@echo "⚠️  This will modify .git/hooks/ and change git behavior"
	$(VENV_PATH)/bin/pre-commit install
	@echo "✅ Pre-commit hooks installed successfully"
	@echo "🔒 Git hooks are now active for this repository"

pre-commit-uninstall: .ensure-precommit
	@echo "Removing pre-commit hooks..."
	@if [ -f ".git/hooks/pre-commit" ]; then \
		$(VENV_PATH)/bin/pre-commit uninstall; \
		echo "✅ Pre-commit hooks removed successfully"; \
		echo "🔓 Git hooks are no longer active"; \
		echo "💡 You can still run checks manually: make lint, make test, make format"; \
	else \
		echo "ℹ️  No pre-commit hooks found to remove"; \
	fi

# Lightweight commands for pre-commit hooks (minimal output)
pre-commit-lint:
	@$(PYTHON) -m ruff check $(SOURCES)
	@npx pyright

pre-commit-format:
	@$(PYTHON) -m ruff check --fix $(SOURCES)
	@$(PYTHON) -m ruff format $(SOURCES)

pre-commit-test:
	@$(PYTHON) -m pytest tests/ -m "not integration" -q

# -----------------------------------------------------------------------------
# Cleanup
# -----------------------------------------------------------------------------

clean:
	@echo "Cleaning up generated files and caches..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -f pytest-results*.xml
	rm -f pytest-report*.html
	rm -rf *.egg-info/
	rm -rf .ruff_cache/
	rm -rf .tox/
	rm -f *-report.json
	rm -f *-report.txt
	@echo "✅ Cleanup complete"

clean-all: clean
	@echo "Performing deep cleanup..."
	@echo "⚠️  This will remove the virtual environment and require 'make setup' to rebuild"
	@read -p "Continue with deep clean? (y/N): " answer; \
	if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
		rm -rf $(VENV_PATH); \
		rm -rf .env; \
		echo "✅ Deep cleanup complete - virtual environment and .env removed"; \
		echo "💡 Run 'make setup' to rebuild the environment"; \
	else \
		echo "⏭️  Deep cleanup cancelled"; \
	fi

clean-force: clean
	@echo "Performing deep cleanup (non-interactive)..."
	rm -rf $(VENV_PATH)
	rm -f .env
	@echo "✅ Deep cleanup complete - virtual environment and .env removed"

# -----------------------------------------------------------------------------
# Application
# -----------------------------------------------------------------------------

run: .ensure-python
	$(PYTHON) main.py

compare-models: .ensure-python
	$(PYTHON) tools/detailed_model_comparison.py

compare-models-basic: .ensure-python
	$(PYTHON) tools/basic_model_comparison.py

verify-prompts: .ensure-python
	$(PYTHON) tools/verify_prompt_consistency.py

generate-tags: .ensure-python
	$(PYTHON) tools/generate_tags.py $(ARGS)

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------

docker-build:
	@echo "Building Docker image..."
	docker build -t mealie-translator:latest .

docker-run:
	@if [ ! -f ".env" ]; then \
		echo "⚠️  .env file not found. Run 'make setup-env' first and configure your API keys."; \
		exit 1; \
	fi
	@echo "Running application in Docker container with cron scheduling..."
	docker-compose up mealie-translator

docker-dev:
	@if [ ! -f ".env" ]; then \
		echo "⚠️  .env file not found. Run 'make setup-env' first and configure your API keys."; \
		exit 1; \
	fi
	@echo "Starting development environment (single run)..."
	docker-compose --profile dev up mealie-translator-dev

docker-logs:
	@echo "Following Docker container logs..."
	docker-compose logs -f mealie-translator

docker-test:
	@echo "Running tests in Docker container..."
	docker build --target testing -t mealie-translator:test .

docker-clean:
	@echo "Cleaning Docker images and containers..."
	docker-compose down --volumes --remove-orphans
	docker image prune -f
	docker container prune -f
	@echo "✅ Docker cleanup complete"

# -----------------------------------------------------------------------------
# Security
# -----------------------------------------------------------------------------

security-scan: security-bandit security-pip-audit
	@echo "✅ All security scans completed"

security-bandit: .ensure-python
	@$(PYTHON) -c "import bandit" 2>/dev/null || { echo "⚠️  bandit not found. Run 'make install-dev' first."; exit 1; }
	@echo "Running bandit security scanner..."
	$(PYTHON) -m bandit -r mealie_translate/ -f json -o bandit-report.json || true
	$(PYTHON) -m bandit -r mealie_translate/ -f txt

security-pip-audit: .ensure-python
	@$(PYTHON) -c "import pip_audit" 2>/dev/null || { echo "⚠️  pip-audit not found. Run 'make install-dev' first."; exit 1; }
	@echo "Running pip-audit dependency vulnerability scanner..."
	$(PYTHON) -m pip_audit --format=json --output=pip-audit-report.json || true
	$(PYTHON) -m pip_audit --format=columns
