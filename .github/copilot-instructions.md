<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit
https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Mealie Recipe Translator Project Instructions

A production-ready Python application that translates Mealie recipes using OpenAI's API and converts imperial units to metric.

## 🏗️ Project Architecture

This is a **mature, production-ready project** with comprehensive tooling:

- **Core Application**: Python 3.11+ with OpenAI API integration for recipe translation
- **CI/CD**: Separated 3-workflow architecture (CI → CD → Security)
- **Deployment**: Docker containers published to GitHub Container Registry (GHCR)
- **Development**: 35+ Makefile commands, pre-commit hooks, comprehensive testing
- **Documentation**: 7 detailed docs covering all aspects

## 🔑 Key Components

### Core Application Files

- `mealie_translate/`: Main package with all business logic
- `main.py`: CLI entry point
- `tests/`: Comprehensive test suite (unit + integration)

### Infrastructure & Tooling

- `Makefile`: **Primary development interface** - use `make help` for all commands
- `.github/workflows/`: Separated CI/CD pipelines
- `Dockerfile`: Multi-stage builds (dev/prod/testing)
- `docs/`: Extensive documentation (see `docs/README.md` for index)

## 🛠️ Development Workflow

### Essential Commands (Use These First)

```bash
make help           # Shows all 35+ available commands
make setup-full     # Complete development setup
npm install         # Node.js deps for markdownlint
make test-unit      # Quick tests during development
make lint-all       # All code quality checks
make check          # Complete dev workflow: format + lint-all + test
make run            # Run the application
```

### Key Development Principles

- **Use the Makefile**: Don't run commands directly, use `make` targets
- **Follow existing patterns**: The project has established conventions
- **Test thoroughly**: Unit tests are fast, integration tests need API keys
- **Docker-first deployment**: Production runs in containers

## 📝 Code Standards

### Python

- **Formatting & Linting**: `ruff` (fast Rust-based tool) + `pyright` (run `make format`, `make lint`)
- **Testing**: `pytest` with both unit and integration tests
- **Security**: `bandit` + `pip-audit` for vulnerability scanning
- **Type hints**: Required for all public functions
- **Logging**: Use structured logging via `get_logger(__name__)` - NO print statements in production code

### Documentation

<!-- markdownlint-disable MD013 -->

- **Line length**: 120 characters max
- **Style**: "One sentence per line" for better diffs
- **Linting**: `markdownlint` with custom rules (`.markdownlint.json`)
- **No trailing punctuation**: In headings (✗ `## Setup:` ✓ `## Setup`)
- **Code blocks**: Always specify language
- **Links**: Use descriptive text, bare URLs are allowed

Examples:

```markdown
<!-- ✓ GOOD -->

This sentence explains the concept clearly.
This is a separate sentence on its own line.

Use the `make lint-all` command to check code quality.

<!-- ✗ BAD -->

This sentence explains the concept clearly. This is a separate sentence that makes the line too long and violates our 120-character limit.

Use the make lint-all command to check code quality.
```

<!-- markdownlint-enable MD013 -->

### Git & CI/CD

- **Branches**: Feature branches with descriptive names
- **Commits**: Conventional commits (feat:, fix:, docs:, etc.)
- **PRs**: Will trigger CI automatically, add `run-integration-tests` label if needed
- **Deployment**: Automatic to staging on main, manual to production via tags

## 🎯 Common Tasks

### When Writing Code

1. **Always use the Makefile**: `make test-unit`, `make format`, `make lint-all`
2. **Follow existing patterns**: Look at existing code for structure
3. **Use proper logging**: Import `get_logger(__name__)` and use `logger.info/debug/warning/error()` instead of print statements
4. **Add tests**: Unit tests in `tests/`, follow existing patterns
5. **Update docs**: If changing behavior, update relevant documentation
6. **Test your changes**: Run all tests locally before pushing

### When Writing Documentation

1. **Use markdownlint rules**: Check with `make lint-markdown`
2. **Follow line length**: Max 120 chars, one sentence per line
3. **Update index**: Add new docs to `docs/README.md`
4. **Test examples**: Ensure code examples actually work

### When Adding Dependencies

1. **Python**: Add to `pyproject.toml`, run `make setup`
2. **Node.js**: Add to `package.json`, run `npm install`
3. **Security**: Dependencies are auto-scanned by `pip-audit`

## 🚨 Important Notes

- **This is a complex, mature project**: Don't oversimplify or suggest removing infrastructure
- **Use existing tooling**: The Makefile provides everything needed
- **Documentation is critical**: Keep docs updated and accurate
- **Security matters**: Follow existing security practices
- **Docker deployment**: Production deployment is containerized

## 📚 Key Resources

- **Complete command reference**: `make help`
- **Development guide**: `docs/DEVELOPMENT.md`
- **Docker deployment**: `docs/DOCKER.md`
- **Docker image strategy**: `docs/DOCKER_IMAGE_STRATEGY.md`
- **CI/CD architecture**: `docs/CI_CD_ARCHITECTURE.md`
- **Security architecture**: `docs/SECURITY_ARCHITECTURE.md`

When in doubt, check the extensive documentation in the `docs/` folder!
