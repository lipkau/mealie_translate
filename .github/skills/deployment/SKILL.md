---
name: deployment
description: Step-by-step workflow for deploying this project. USE FOR: creating a new release; drafting release notes; classifying semver (patch, minor, major); publishing a version tag or GitHub Release; understanding the CI → CD → staging → production pipeline; knowing what triggers Docker image builds; checking deployment status. DO NOT USE FOR: general coding; writing tests; local development setup.
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

### 2. Release plan (before tagging)

Do this immediately before tagging so the commit range and CI status are current.

1. **Previous release ref** — Latest shipped tag, for example:
   `PREV=$(git describe --tags --abbrev=0 2>/dev/null)`
   If that is wrong or missing, set `PREV` to the explicit tag or commit users last received.
2. **Commits in range** — `git log "$PREV"..HEAD --oneline` (optionally group by conventional-commit type).
3. **User-facing vs internal** — Highlight changes that affect operators or recipe behavior: CLI flags, Docker image behavior, env config in `mealie_translate/`, translation or organizer output. Treat dev-only paths (for example `tools/` scripts) as internal unless documentation promises them to end users.
4. **Semver** — Choose the next version with [Semantic Versioning](https://semver.org/):
   - `PATCH` (`v1.0.1`): bug fixes, no breaking changes
   - `MINOR` (`v1.1.0`): new features, backwards-compatible
   - `MAJOR` (`v2.0.0`): breaking changes for consumers of the app or image
   If something looks removed but only non-shipped code changed (for example model lists inside `tools/`, not runtime settings), say why it stays PATCH or MINOR.
5. **Draft GitHub release notes** — Structure the draft for humans, for example: **What's New**, **Bug Fixes**, **Infrastructure**, **Documentation**. Use a short **bold** lead-in per item; add `(#123)` when the PR number is known.
6. **Full changelog link** — After you know `PREV` and the new tag `NEW_TAG`:
   `https://github.com/lipkau/mealie_translate/compare/${PREV}...${NEW_TAG}`
   Adjust owner/repo if the remote differs.
7. **Last check** — Re-open Actions and confirm `main` is still green; re-run the log command if new commits landed.

### 3. Create and push the version tag

Use three-part tags (`v1.2.3`) for clarity.

```bash
# Replace v1.2.3 with the actual version
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

### 4. Create a GitHub Release (recommended)

Publish the drafted notes from step 2 so the tag appears under GitHub Releases (optional but usual for this repo).

```bash
gh release create v1.2.3 \
  --title "v1.2.3" \
  --notes-file - <<'EOF'
<!-- Paste the drafted notes from step 2 -->

**Full Changelog**: https://github.com/lipkau/mealie_translate/compare/PREV_TAG...v1.2.3
EOF
```

Replace `PREV_TAG` with the real previous tag. You can use `--generate-notes` for a skeleton, then edit in the UI if you prefer.

### 5. What happens automatically

1. **CD pipeline** detects the `v*` tag.
2. **Docker images** are built (production stage) and pushed to GHCR with tags `latest`, `v1.2.3`, `1.2`.
3. **Production deployment job** is queued and waits for required reviewers to approve.
4. **Security pipeline** runs after CD completes (Trivy scan + dependency audit).

### 6. Monitor the release

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
