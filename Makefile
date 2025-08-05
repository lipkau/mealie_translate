.PHONY: help setup setup-full setup-env install install-dev test test-unit test-integration test-coverage lint lint-format lint-markdown lint-all format pre-commit pre-commit-force pre-commit-uninstall clean clean-all run compare-models compare-models-basic verify-prompts docker-build docker-run docker-dev docker-test docker-clean security-scan security-bandit security-pip-audit

# Auto-detect virtual environment or use default
VENV_PATH := $(shell if [ -d ".venv" ]; then echo ".venv"; elif [ -d "venv" ]; then echo "venv"; elif [ -d "env" ]; then echo "env"; elif [ -n "$(VIRTUAL_ENV)" ]; then echo "$(VIRTUAL_ENV)"; else echo ".venv"; fi)
PYTHON := $(VENV_PATH)/bin/python
PIP := $(VENV_PATH)/bin/pip

# Python version requirements
REQUIRED_PYTHON_VERSION := 3.11
PREFERRED_PYTHON_VERSION := 3.13.0

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

# Default target
help:
	@echo "Available commands:"
	@echo "  setup                Create virtual environment and install dependencies"
	@echo "  setup-full           Complete setup including pre-commit hooks (recommended for contributors)"
	@echo "  setup-env            Copy .env.example to .env (run after setup, or included in setup)"
	@echo "  install              Install production dependencies"
	@echo "  install-dev          Install development dependencies"
	@echo "  test                 Run all tests (generates JUnit XML and HTML reports)"
	@echo "  test-unit            Run unit tests only (generates JUnit XML and HTML reports)"
	@echo "  test-integration     Run integration tests (generates JUnit XML and HTML reports)"
	@echo "  test-coverage        Run tests with coverage report (generates JUnit XML, HTML, and coverage reports)"
	@echo "  lint                 Run code linting (ruff, pyright)"
	@echo "  lint-format          Check code formatting (ruff)"
	@echo "  lint-markdown        Check markdown formatting (markdownlint)"
	@echo "  lint-all             Run all linting and formatting checks"
	@echo "  format               Format code with ruff"
	@echo "  security-scan        Run all security scans (bandit + pip-audit)"
	@echo "  security-bandit      Run bandit security scanner (creates bandit-report.json)"
	@echo "  security-pip-audit   Run pip-audit dependency vulnerability scanner (creates pip-audit-report.json)"
	@echo "  pre-commit           Install git hooks (interactive, with detailed warnings)"
	@echo "  pre-commit-force     Install git hooks without prompting (for automation)"
	@echo "  pre-commit-uninstall Remove git hooks from repository"
	@echo "  pre-commit-lint      Lightweight lint for pre-commit (no output)"
	@echo "  pre-commit-format    Lightweight format for pre-commit (no output)"
	@echo "  pre-commit-test      Lightweight test for pre-commit (quiet mode)"
	@echo "  clean                Clean up cache files, test reports, and build artifacts"
	@echo "  clean-all            Deep clean including virtual environment"
	@echo "  run                  Run the main application"
	@echo "  check-python         Check Python version compatibility"
	@echo "  compare-models       Run detailed model comparison"
	@echo "  compare-models-basic Run basic model comparison"
	@echo "  verify-prompts       Verify model comparison uses production prompts"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build         Build Docker image"
	@echo "  docker-run           Run application in Docker container with cron scheduling"
	@echo "  docker-dev           Run development environment (single run)"
	@echo "  docker-logs          Follow Docker container logs"
	@echo "  docker-test          Run tests in Docker container"
	@echo "  docker-clean         Clean Docker images and containers"
	@echo ""
	@echo "Virtual environment detected: $(VENV_PATH)"
ifneq ($(PYENV_AVAILABLE),)
	@echo "Pyenv detected: Available"
ifneq ($(PYTHON_VERSION_FILE),)
	@echo "Python version file: $(shell cat .python-version)"
endif
else
	@echo "Pyenv detected: Not available"
endif
	@echo "Python for venv creation: $(PYTHON_FOR_VENV)"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup-full  # Complete setup for contributors: venv, dependencies, env config, npm deps & pre-commit hooks"
	@echo "     OR"
	@echo "     make setup       # Basic setup: venv, dependencies, env config (no npm deps or pre-commit hooks)"
	@echo "  2. Edit .env file with your API keys"
	@echo "  3. make run         # Start the application"

# Python version checking
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

# Setup - Create venv and install dev dependencies (basic)
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

# Setup - Complete setup including pre-commit hooks (for contributors)
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

# Environment setup
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

# Install dependencies
install:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PIP) install -e .

install-dev:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PIP) install -e .[dev]

# Testing
test:
	@if ! $(PYTHON) -c "import pytest" 2>/dev/null; then \
		echo "⚠️  pytest not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ -v --junit-xml=pytest-results.xml --html=pytest-report.html --self-contained-html

test-unit:
	@if ! $(PYTHON) -c "import pytest" 2>/dev/null; then \
		echo "⚠️  pytest not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ -v -m "not integration" --junit-xml=pytest-results-unit.xml --html=pytest-report-unit.html --self-contained-html

test-integration:
	@if ! $(PYTHON) -c "import pytest" 2>/dev/null; then \
		echo "⚠️  pytest not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ -v -m "integration" --junit-xml=pytest-results-integration.xml --html=pytest-report-integration.html --self-contained-html

test-coverage:
	@if ! $(PYTHON) -c "import pytest, pytest_cov" 2>/dev/null; then \
		echo "⚠️  pytest or pytest-cov not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m pytest tests/ --cov=mealie_translate --cov-report=html --cov-report=term --cov-report=xml --junit-xml=pytest-results-coverage.xml --html=pytest-report-coverage.html --self-contained-html

# Code quality
lint:
	@echo "Running code linting..."
	@if ! $(PYTHON) -c "import ruff" 2>/dev/null; then \
		echo "⚠️  ruff not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m ruff check mealie_translate/ tests/ main.py
	@if ! command -v npx >/dev/null 2>&1; then \
		echo "⚠️  npx not found. Install Node.js or run 'npm install'."; \
		exit 1; \
	fi
	@if ! npx pyright --version >/dev/null 2>&1; then \
		echo "⚠️  pyright not found. Run 'npm install' to install dependencies."; \
		exit 1; \
	fi
	npx pyright

lint-format:
	@echo "Checking code formatting..."
	@if ! $(PYTHON) -c "import ruff" 2>/dev/null; then \
		echo "⚠️  ruff not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m ruff format --check mealie_translate/ tests/ main.py

lint-markdown:
	@echo "Checking markdown formatting..."
	@if command -v npx >/dev/null 2>&1 && [ -f package.json ]; then \
		echo "Using npx markdownlint (from package.json)..."; \
		npx markdownlint **/*.md; \
	elif command -v markdownlint >/dev/null 2>&1; then \
		echo "Using global markdownlint..."; \
		markdownlint **/*.md; \
	else \
		echo "⚠️  markdownlint not found. Install with: npm install or npm install -g markdownlint-cli"; \
		exit 1; \
	fi

lint-all: lint lint-format lint-markdown

format:
	@echo "Formatting code with ruff..."
	@if ! $(PYTHON) -c "import ruff" 2>/dev/null; then \
		echo "⚠️  ruff not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(PYTHON) -m ruff check --fix mealie_translate/ tests/ main.py
	$(PYTHON) -m ruff format mealie_translate/ tests/ main.py

# Pre-commit hooks
pre-commit:
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
	@if ! $(VENV_PATH)/bin/pre-commit --version >/dev/null 2>&1; then \
		echo "⚠️  pre-commit not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	@read -p "Do you want to install these git hooks? (y/N): " answer; \
	if [ "$$answer" = "y" ] || [ "$$answer" = "Y" ]; then \
		$(VENV_PATH)/bin/pre-commit install; \
		echo "✅ Pre-commit hooks installed successfully"; \
		echo "� Git hooks are now active and will run on every commit"; \
		echo "💡 Test them with: pre-commit run --all-files"; \
		echo "🗑️  Remove them with: pre-commit uninstall"; \
	else \
		echo "⏭️  Pre-commit hooks installation cancelled"; \
		echo "💡 You can still run checks manually: make lint, make test, make format"; \
	fi

# Pre-commit hooks (force install for automation)
pre-commit-force:
	@echo "Installing pre-commit hooks (non-interactive)..."
	@echo "⚠️  This will modify .git/hooks/ and change git behavior"
	@if ! $(VENV_PATH)/bin/pre-commit --version >/dev/null 2>&1; then \
		echo "⚠️  pre-commit not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	$(VENV_PATH)/bin/pre-commit install
	@echo "✅ Pre-commit hooks installed successfully"
	@echo "🔒 Git hooks are now active for this repository"

# Pre-commit hooks (uninstall)
pre-commit-uninstall:
	@echo "Removing pre-commit hooks..."
	@if ! $(VENV_PATH)/bin/pre-commit --version >/dev/null 2>&1; then \
		echo "⚠️  pre-commit not found. Run 'make setup' first to install dependencies."; \
		exit 1; \
	fi
	@if [ -f ".git/hooks/pre-commit" ]; then \
		$(VENV_PATH)/bin/pre-commit uninstall; \
		echo "✅ Pre-commit hooks removed successfully"; \
		echo "🔓 Git hooks are no longer active"; \
		echo "💡 You can still run checks manually: make lint, make test, make format"; \
	else \
		echo "ℹ️  No pre-commit hooks found to remove"; \
	fi

# Lightweight commands for pre-commit hooks (no echo, direct execution)
pre-commit-lint:
	@$(PYTHON) -m ruff check mealie_translate/ tests/ main.py
	@npx pyright

pre-commit-format:
	@$(PYTHON) -m ruff check --fix mealie_translate/ tests/ main.py
	@$(PYTHON) -m ruff format mealie_translate/ tests/ main.py

pre-commit-test:
	@$(PYTHON) -m pytest tests/ -m "not integration" -q

# Cleanup
clean:
	@echo "Cleaning up generated files and caches..."
	# Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	# Test and coverage files
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -f pytest-results*.xml
	rm -f pytest-report*.html
	# Build artifacts
	rm -rf *.egg-info/
	# Cache directories
	rm -rf .ruff_cache/
	rm -rf .tox/
	# Security and audit reports
	rm -f *-report.json
	rm -f *-report.txt
	@echo "✅ Cleanup complete"

# Deep cleanup including virtual environment
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

# Run application
run:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PYTHON) main.py

# Model comparison tools
compare-models:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PYTHON) tools/detailed_model_comparison.py

compare-models-basic:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PYTHON) tools/basic_model_comparison.py

verify-prompts:
	@if ! $(PYTHON) --version >/dev/null 2>&1; then \
		echo "⚠️  Python not found at $(PYTHON). Run 'make setup' first."; \
		exit 1; \
	fi
	$(PYTHON) tools/verify_prompt_consistency.py

# Docker commands
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

# Security scanning
security-scan: security-bandit security-pip-audit
	@echo "✅ All security scans completed"

security-bandit:
	@if ! $(PYTHON) -c "import bandit" 2>/dev/null; then \
		echo "⚠️  bandit not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	@echo "Running bandit security scanner..."
	$(PYTHON) -m bandit -r mealie_translate/ -f json -o bandit-report.json || true
	$(PYTHON) -m bandit -r mealie_translate/ -f txt

security-pip-audit:
	@if ! $(PYTHON) -c "import pip_audit" 2>/dev/null; then \
		echo "⚠️  pip-audit not found. Run 'make install-dev' first."; \
		exit 1; \
	fi
	@echo "Running pip-audit dependency vulnerability scanner..."
	$(PYTHON) -m pip_audit --format=json --output=pip-audit-report.json || true
	$(PYTHON) -m pip_audit --format=columns
