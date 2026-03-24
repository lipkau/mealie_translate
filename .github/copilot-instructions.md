<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit
https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Mealie Recipe Translator Project Instructions

A production-ready Python application that translates Mealie recipes using OpenAI's API and converts imperial units to metric.

## 🏗️ Project Architecture

This is a **mature, production-ready project**.
Do not oversimplify or suggest removing existing infrastructure.

### Core Application Files

- `mealie_translate/`: Main package with all business logic
- `main.py`: CLI entry point
- `tests/`: Comprehensive test suite (unit + integration)
- `Makefile`: **Primary development interface** — use `make help` for all commands
- `.github/workflows/`: Separated CI/CD pipelines (CI → CD → Security)
- `docs/`: Extensive documentation (see `docs/README.md` for index)

## 📝 Python Code Standards

- **Formatting & Linting**: `ruff` + `pyright`
- **Type hints**: Required for all public functions
- **Logging**: Use `get_logger(__name__)` — NO `print` statements in production code
- **Security**: `bandit` + `pip-audit` for vulnerability scanning
- **HTTP Clients**: Always use `http2=True` for httpx clients (see below)

## 🌐 HTTP Client Guidelines

When creating HTTP clients for external APIs (Mealie, OpenAI, new LLM providers):

```python
# Standalone httpx client
client = httpx.AsyncClient(http2=True, ...)

# OpenAI SDK or similar with custom client
http_client = httpx.AsyncClient(http2=True)
sdk_client = AsyncOpenAI(http_client=http_client, ...)
```

This ensures multiplexing, header compression, and connection reuse for all API calls.
See `docs/DEVELOPMENT.md` for full implementation details.

## 🔀 Git Conventions

- **Branches**: `feature/`, `fix/`, `docs/`, `chore/` prefix with a short descriptor
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `ci:`, `chore:`)
- **PRs**: Add `run-integration-tests` label to trigger integration tests on a PR

## 🛠️ Agent Skills

Detailed workflows are defined as agent skills in `.github/skills/`.
Copilot loads the relevant skill automatically, or invoke one manually with `/skill-name`:

| Skill | When it is used |
| --- | --- |
| `/cleanup` | Repo maintenance passes: dead code, stale TODOs, redundant code, safe cleanup |
| `/refactor` | Behavior-preserving code refactors focused on readability and structure |
| `/use-makefile` | Running any development task (tests, lint, format, Docker, …) |
| `/python-venv` | Running Python directly without a `make` target |
| `/deployment` | Creating a release, pushing a version tag, understanding the CD pipeline |
| `/recipe-taxonomy` | Assigning or reviewing categories and tags on recipes |
| `/write-documentation` | Creating or editing Markdown files in `docs/` |
| `/add-dependencies` | Adding Python or Node.js packages |
| `/write-tests` | Writing unit or integration tests |

## 🎯 Preferred Copilot Steering

Use short intent-focused prompts and rely on repo skills for the workflow details.

- "update documentation" → `/write-documentation`
- "refactor `mealie_translate/recipe_processor.py`" → `/refactor`
- "clean up `mealie_translate/`" → `/cleanup`

When using these skills:

- Prefer behavior-preserving changes over broad rewrites.
- Validate code changes with `make format`, `make lint`, and `make test-unit`.
- Validate documentation changes with `make lint-markdown`.
- Treat "tree shaking" in this Python repo as dead-code elimination, not frontend bundler optimization.

## 📚 Key Documentation

- `docs/TAXONOMY.md` — Recipe categories and tags vocabulary
- `docs/DEVELOPMENT.md` — Full development guide
- `docs/CI_CD_ARCHITECTURE.md` — Pipeline architecture
- `docs/DOCKER.md` — Docker deployment guide
- `docs/SECURITY_ARCHITECTURE.md` — Security practices

When in doubt, check the `docs/` folder or run `make help`.
