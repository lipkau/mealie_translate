# Contributing to Mealie Recipe Translator

Thank you for your interest in contributing to the Mealie Recipe Translator!

> **📋 Quick Guide**:
>
> - **First-time setup?** → See [README Installation](../README.md#installation)
> - **Contributing code?** → This guide covers the fork-based workflow
> - **Need detailed dev docs?** → See [DEVELOPMENT.md](../docs/DEVELOPMENT.md)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the [existing issues](https://github.com/LIO2MU/mealie_translate/issues)
as you might find that the problem has already been reported.

When you are creating a bug report, please include as many details as possible:

- Use the bug report template
- Include steps to reproduce the issue
- Provide specific examples and sample data
- Include relevant logs and error messages
- Describe the expected vs actual behavior

### Suggesting Enhancements

Enhancement suggestions are welcome! Please use the feature request template and include:

- A clear description of the enhancement
- Explain why this enhancement would be useful
- Provide examples of how it would work
- Consider if this fits with the project scope

### Contributing Code

1. **Fork the repository** on GitHub
2. **Clone your fork** and set up development environment
3. **Create a feature branch** from `main`
4. **Make your changes** following our coding standards
5. **Add tests** for any new functionality
6. **Update documentation** as needed
7. **Run the test suite** to ensure everything works
8. **Push to your fork** and submit a pull request

## Development Setup

### Prerequisites

- Python 3.11+ (Recommended: 3.13.0 - see [README](../README.md#python-version-management))
- Git
- OpenAI API key for testing (optional)
- Docker (optional, for containerized development)

### Quick Start for Contributors

1. **Fork and clone your fork:**

   ```bash
   # Fork on GitHub first, then:
   git clone https://github.com/YOUR-USERNAME/mealie_translate.git
   cd mealie_translate

   # Add upstream remote for staying in sync
   git remote add upstream https://github.com/lipkau/mealie_translate.git
   ```

2. **Set up development environment:**

   ```bash
   make setup-full  # Complete contributor setup with pre-commit hooks
   # Edit .env with your API keys (see .env.example)
   ```

3. **Verify everything works:**

   ```bash
   make test-unit    # Quick verification
   make help         # See all available commands
   ```

> **📋 Detailed Setup**: For complete installation instructions, see the [README Installation section](../README.md#installation).

### Development Commands

The project includes a comprehensive Makefile. Essential commands for contributors:

```bash
make setup-full     # Complete contributor setup with pre-commit hooks
make test-unit      # Quick unit tests during development
make format         # Auto-format code (ruff)
make lint           # Check code quality (ruff, pyright)
make test           # Full test suite before committing
```

> **📋 Complete Command Reference**: Run `make help` or see [DEVELOPMENT.md](../docs/DEVELOPMENT.md) for all available commands.

#### Contributor Workflow Summary

```bash
# 1. Fork repository on GitHub, then clone your fork
git clone https://github.com/YOUR-USERNAME/mealie_translate.git
cd mealie_translate
git remote add upstream https://github.com/lipkau/mealie_translate.git

# 2. Set up development environment
make setup-full

# 3. Create feature branch
git checkout -b feature/your-feature

# 4. Development cycle
make test-unit && make format && make lint && make test

# 5. Commit and push to your fork
git add . && git commit -m "feat: your feature description"
git push origin feature/your-feature

# 6. Create pull request on GitHub
```

> **💡 Pro tip**: The pre-commit hooks (installed by `make setup-full`) will automatically run formatting
> and linting checks when you commit.

### Keeping Your Fork in Sync

Keep your fork updated with the upstream repository:

```bash
# Fetch upstream changes
git fetch upstream

# Switch to main and merge upstream changes
git checkout main
git merge upstream/main

# Push updates to your fork
git push origin main

# Update your feature branch (if needed)
git checkout feature/your-feature
git rebase main  # or git merge main
```

### Docker Development

For containerized development:

```bash
# Build development image
make docker-build

# Run tests in container
make docker-test

# Run the application in container
docker run --env-file .env mealie-recipe-translator
```

## Coding Standards

### Python Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use [ruff](https://docs.astral.sh/ruff/) for code formatting and linting
- Use [pyright](https://github.com/microsoft/pyright) for type checking
- Use [pyright](https://github.com/microsoft/pyright) for type checking

### Code Organization

- Keep functions small and focused
- Use descriptive variable and function names
- Add type hints to all function signatures
- Include docstrings for all public functions and classes
- Write comprehensive tests for new functionality

### Documentation

- Update README.md if you change installation or usage
- Add inline comments for complex logic
- Update docstrings when changing function behavior
- Create or update documentation files in the `docs/` folder
- Follow the "one sentence per line" style for Markdown files

## Testing

### Test Structure

- **Unit tests**: Test individual functions and classes in isolation
- **Integration tests**: Test interactions between components
- **End-to-end tests**: Test complete workflows

### Writing Tests

- Use descriptive test names that explain what is being tested
- Follow the Arrange-Act-Assert pattern
- Mock external dependencies (APIs, file system, etc.)
- Test both success and failure scenarios
- Aim for high test coverage of new code

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration

# Run with coverage
make test-coverage

# Run specific test file
python -m pytest tests/test_translator.py -v

# Run specific test function
python -m pytest tests/test_translator.py::test_translate_recipe -v
```

## Pull Request Process

1. **Create a feature branch:**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Write or update tests** for your changes

4. **Update documentation** as needed

5. **Run the full test suite:**

   ```bash
   make test
   make lint
   ```

6. **Commit your changes** with clear commit messages:

   ```bash
   git commit -m "Add feature: brief description of what you added"
   ```

7. **Push to your fork:**

   ```bash
   git push origin feature/your-feature-name
   ```

8. **Create a pull request** using our template

### Pull Request Guidelines

- Fill out the pull request template completely
- Include a clear description of the changes
- Link to any related issues
- Ensure all CI checks pass
- Be responsive to feedback and requests for changes
- Squash commits if requested

## Release Process

The project follows semantic versioning (SemVer):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Releases are automated through GitHub Actions when tags are pushed.

## Community and Communication

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and general discussion
- **Documentation**: Check the README and docs folder for guidance

## Recognition

Contributors will be recognized in:

- The project's README.md contributors section
- Release notes for significant contributions
- Special recognition for long-term contributors

## Getting Help

If you need help contributing:

1. Check the existing documentation
2. Search through issues and discussions
3. Create a new discussion or issue
4. Be patient and respectful when asking for help

## License

By contributing to this project, you agree that your contributions will be licensed under the same license
as the project (see [LICENSE](LICENSE) file).

Thank you for contributing to Mealie Recipe Translator! 🎉
