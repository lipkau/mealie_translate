# Docker Image Strategy

This document explains when and how Docker images are built
in the Mealie Recipe Translator project.

## Overview

The `Image` job in `.github/workflows/ci.yml` builds the image from the
default Dockerfile target and pushes it to `ghcr.io/lipkau/mealie_translate`.
It runs after the Markdown, code quality, unit test and Dockerfile jobs pass,
and the `CI result` check needs it.

The job uses the shared
[container-image](https://github.com/lipkau/gh-tools/tree/main/actions/container-image)
action, so every repository tags its images the same way.
All published images are identical: same base, same dependencies,
same entrypoint, same behavior.

## Image Tags

| Build                     | Tags                                                      |
| ------------------------- | --------------------------------------------------------- |
| Pull request              | the branch name (`fix/x` → `fix-x`), `sha-<commit>`       |
| Push to `main`            | `main`, `sha-<commit>`                                    |
| Version tag `v1.2.3`      | `1.2.3`, `1.2`, `1`, `v1.2.3`, `latest`, `sha-<commit>`   |
| Version tag `v1.3.0-rc.1` | `1.3.0-rc.1`, `v1.3.0-rc.1`, `sha-<commit>` (no `latest`) |

- `latest` is always the newest release. A pre-release never moves it.
- `main` is the newest validated build of `main`, for beta users and staging.
- A pull request's `sha-` tag names its head commit.
- A version tag must point at a commit on `main`. Otherwise the job fails and
  nothing is published.

Images built before the switch to the shared action also carry `dev`
(builds of `main`) and `pr-<N>`. Those tags no longer move.

## Build Scenarios

### 1. Push to `main` (merge)

**Result**: `:main` and `:sha-<commit>`, for amd64 and arm64.

### 2. Version tag on `main` (release)

```bash
git tag -a v1.2.3 -m "Release v1.2.3"
git push origin v1.2.3
```

**Result**: one build, tagged `1.2.3`, `1.2`, `1`, `v1.2.3`, `latest` and `sha-<commit>`.
See [RELEASING.md](RELEASING.md) for the whole release.

### 3. Pull request

Open or push to a PR targeting `main`. The image is pushed under the
branch name and `sha-<commit>`, and the job's summary lists both.
A PR from a fork builds the image without pushing it.

## PR Image Lifecycle

1. PR opened or pushed: CI builds and pushes the branch's image.
2. Later pushes: the branch tag moves to the new build.
3. PR closed (merged or not): `image-cleanup.yml` deletes the branch's images from GHCR.
   It also runs every Monday, which catches a build that finished after its PR closed.

## Image Cleanup

`image-cleanup.yml` runs the shared
[ghcr-cleanup](https://github.com/lipkau/gh-tools/tree/main/actions/ghcr-cleanup) action.
It deletes images of closed PRs and old builds of `main`. It keeps `main`, `dev`,
`latest` and release tags.
Untagged images, such as earlier `dev` builds, are listed in the run summary but not deleted,
because a deployment may still pin one by digest.
Run it from the Actions tab to preview: the manual run is a dry run by default.

## Supply-Chain Attestation

All images are built with:

- **SLSA provenance** (`provenance: mode=max`): records builder, source, and
  build instructions.
- **SBOM** (`sbom: true`): a Software Bill of Materials.

Inspect with:

```bash
docker buildx imagetools inspect ghcr.io/lipkau/mealie_translate:latest
```

## Concurrency

A new push to a PR cancels the PR's running CI, including its image build.
Pushes to `main` and version tags each get their own run and never cancel each other,
so every one of them publishes its image.

## Troubleshooting

### Image not built

1. Check that the jobs the `Image` job needs passed.
2. For a release, check that the tag follows the `v*` pattern and the
   tagged commit is on `main`.

### PR image not appearing

1. Check the `Image` job's summary for the tags.
2. A PR from a fork is built but not pushed.

## Related Documentation

- [CI/CD Architecture](CI_CD_ARCHITECTURE.md): full pipeline overview
- [Docker Guide](DOCKER.md): container usage and deployment
- [Development Guide](DEVELOPMENT.md): local development setup
