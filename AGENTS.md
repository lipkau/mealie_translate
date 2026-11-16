# Mealie Recipe Translator

Translates Mealie recipes with an LLM, converts imperial units to metric, and assigns categories and tags.
It runs on a schedule in a container.
`README.md` covers setup and configuration; `docs/README.md` indexes the rest of the documentation.

## Validate

Run `make lint-all && make test-unit` before committing.
`make test` also runs the integration tests, which call the real APIs and need keys in `.env`.
CI runs them on pushes to `main`, and on a pull request only with the `run-integration-tests` label.

Use the Makefile targets (`make help`) rather than raw `pytest`, `ruff` or `pyright`: they pick the project's virtual
environment, which `make setup` creates in `.venv/`.

## Code rules

- Log with `get_logger(__name__)`; `print` belongs only in the scripts under `tools/`.
- Create every httpx client with `http2=True`, including the one passed to the OpenAI SDK. `docs/DEVELOPMENT.md`
  explains why.
- Mock HTTP in tests with `respx` (the clients use httpx). Unit tests make no network calls; mark tests that do with
  `@pytest.mark.integration`.
- Add runtime dependencies to `[project] dependencies` in `pyproject.toml` and tooling to the `dev` extra, then run
  `make setup`. Node is only for markdownlint.

## Documentation

- One sentence per line, at most 120 characters. `make lint-markdown` checks the rest of the style.
- List a new file under `docs/` in `docs/README.md`.

## Commits and branches

- Conventional Commits with a scope from the git log, such as `fix(converter): handle fractional cups`. The subject
  says why, not which lines changed.
- Branch prefixes: `feature/`, `fix/`, `docs/`, `chore/`.

## Images

CI publishes `ghcr.io/lipkau/mealie_translate`; `docs/DOCKER_IMAGE_STRATEGY.md` lists the tags.
This repository only publishes images. The deployment lives in `lipkau/home.lab`.

## Reference

- `docs/RELEASING.md`: read before cutting a version or writing its release notes.
- `docs/TAXONOMY.md`: read before assigning or reviewing recipe categories and tags, or changing the prompts that do.
