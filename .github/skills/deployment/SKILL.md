---
name: deployment
description: Step-by-step workflow for deploying this project. USE FOR: creating a new release; publishing a version tag; understanding the CI → CD → staging → production pipeline; knowing what triggers Docker image builds; checking deployment status. DO NOT USE FOR: general coding; writing tests; local development setup.
---

# Deployment Workflow

This project uses a 3-pipeline architecture: **CI → CD → Security**.
Production deployments are triggered exclusively by version tags.
See [`docs/CI_CD_ARCHITECTURE.md`](../../../docs/CI_CD_ARCHITECTURE.md) for the full architecture reference.

## Environments

| Environment | Trigger              | Approval |
| ----------- | -------------------- | -------- |
| Staging     | Push to `main`       | Optional |
| Production  | Version tag (`v*.*.*`) | Required reviewers + deployment window |

## Docker Images Published to GHCR

| Tag       | Built from     | Stage       |
| --------- | -------------- | ----------- |
| `dev`     | `main` branch  | development |
| `latest`  | version tags   | production  |
| `v1.2.3`  | version tags   | production  |
| `1.2`     | version tags   | production  |

## How to Create a Production Release

Follow these steps in order:

### 1. Ensure `main` is green

```bash
# Check that CI is passing on main before tagging
# Visit: https://github.com/lipkau/mealie_translate/actions
```

### 2. Determine the next version

Follow [Semantic Versioning](https://semver.org/):

- `PATCH` (`v1.0.1`): bug fixes, no breaking changes
- `MINOR` (`v1.1.0`): new features, backwards-compatible
- `MAJOR` (`v2.0.0`): breaking changes

### 3. Create and push the version tag

```bash
# Replace v1.2.3 with the actual version
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### 4. What happens automatically

1. **CD pipeline** detects the `v*` tag.
2. **Docker images** are built (production stage) and pushed to GHCR with tags `latest`, `v1.2.3`, `1.2`.
3. **Production deployment job** is queued and waits for required reviewers to approve.
4. **Security pipeline** runs after CD completes (Trivy scan + dependency audit).

### 5. Monitor the release

```bash
# Check workflow runs
# https://github.com/lipkau/mealie_translate/actions

# Check published images
# https://github.com/lipkau/mealie_translate/pkgs/container/mealie_translate
```

## Staging Deployment (automatic)

Every push to `main` automatically:

1. Triggers the CI pipeline.
2. On CI success, triggers the CD pipeline.
3. Builds and pushes the `dev` Docker image.
4. Deploys to the staging environment.

No manual action is required for staging.

## Integration Tests in CI/CD

Integration tests run:

- **Always** on `main` branch pushes.
- **On PRs** only when the PR has the label `run-integration-tests`.

## Commit and Branch Conventions

Use conventional commits to produce clear changelogs:

```text
feat:     new feature
fix:      bug fix
docs:     documentation only
refactor: code change without feature or fix
test:     adding or modifying tests
ci:       CI/CD configuration changes
chore:    maintenance (deps, build scripts, etc.)
```

Branch naming: `feature/`, `fix/`, `docs/`, `chore/` prefix with a short descriptor.
