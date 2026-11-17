# CI/CD Pipeline Architecture

This repository tests its code and publishes its container image. It doesn't deploy:
the deployment lives in `lipkau/home.lab`, which pins the image by digest.

## Workflows

### 🔍 Continuous Integration - `.github/workflows/ci.yml`

**Triggers**: pull requests to `main`, pushes to `main`, `v*` tags, manual runs.

| Job                          | What it does                                                             |
| ---------------------------- | ------------------------------------------------------------------------ |
| Markdown Lint and Format     | Biome on all Markdown                                                    |
| Code Quality & Test Coverage | Linting, then unit tests with coverage (Python 3.14)                     |
| Unit Tests (matrix)          | Unit tests on Python 3.11 to 3.14                                        |
| Integration Tests            | On pushes, and on PRs labeled `run-integration-tests`                    |
| Dockerfile Testing Target    | Builds the Dockerfile's `testing` stage                                  |
| Image                        | Builds and pushes the image once the checks above pass                   |
| CI result                    | Fails if any other job failed; the one check the `main` ruleset requires |

The `Image` job uses the shared
[container-image](https://github.com/lipkau/gh-tools/tree/main/actions/container-image) action.
[Docker Image Strategy](DOCKER_IMAGE_STRATEGY.md) lists the tags each build gets.

A new push to a PR cancels the PR's running CI. Pushes to `main` and version tags never cancel
each other, so each one publishes its image. When you add a job, add it to `CI result`'s `needs`.

### 🧹 Image Cleanup - `.github/workflows/image-cleanup.yml`

**Triggers**: `pull_request: closed`, Mondays, manual (dry run by default).
Deletes closed PRs' images and old builds of `main`; `main`, `dev`, `latest` and release images stay.
See [Image Cleanup](DOCKER_IMAGE_STRATEGY.md#image-cleanup).

### 🔒 Security Scanning - `.github/workflows/security.yml`

**Triggers**: after CI on `main`, monthly, manual.

- **Python Security Scan**: static analysis and dependency vulnerability scanning
- **Docker Security Scan**: Trivy scans of the `main` and `latest` images
- **Security Summary**: one report across the scans

See [Security Architecture](SECURITY_ARCHITECTURE.md).

### 🔧 Maintenance - `.github/workflows/maintenance.yml`

Dismisses code scanning alerts that no longer apply.

## Dependency Updates

Renovate (`renovate.json`) extends the shared preset in `lipkau/gh-tools`. It opens one PR on
Monday mornings for all minor and patch updates that are at least 3 days old. Majors wait for
approval in the Dependency Dashboard issue.

## Integration Testing

Integration tests run on every push and on PRs labeled `run-integration-tests`.
They read their configuration from environment variables.

## Permissions

| Job                  | Permissions                                                 |
| -------------------- | ----------------------------------------------------------- |
| Image                | `contents: read`, `packages: write` (push to GHCR)          |
| Docker security scan | `contents: read`, `security-events: write`, `actions: read` |

Security scans upload SARIF to the Security tab. Without GitHub Advanced Security the upload fails
quietly (`continue-on-error: true`), and the reports stay available as workflow artifacts.

## Releasing

Tag a commit on `main` with `v1.2.3` and push the tag. CI publishes the release image
and moves `latest`. [RELEASING.md](RELEASING.md) has the whole procedure.

## Troubleshooting

### CI failures

- Check test output in the test matrix job.
- Review linting errors in the code quality job.
- Check that the `testing` stage builds in the Dockerfile Testing Target job.

### Image not published

- The `Image` job only runs when the jobs it needs passed.
- A release tag must point at a commit on `main`.
- A PR from a fork is built but not pushed.
