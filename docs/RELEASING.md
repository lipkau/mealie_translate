# Releasing

A release is a `vX.Y.Z` tag on a commit on `main`.
Pushing it makes CI and CD publish the image tags listed in [`DOCKER_IMAGE_STRATEGY.md`](DOCKER_IMAGE_STRATEGY.md),
including `latest`.
Nothing is deployed from this repository: `lipkau/home.lab` picks the new version up.

Pushing the tag and publishing the GitHub release are outward-facing: confirm the version and notes with the user first.

## 1. Check `main`

Run `gh run list --branch main --limit 5` and confirm the latest CI run on `main` succeeded.
Done when the commit you will tag has a green CI run.

## 2. Collect the changes

```bash
PREV=$(git describe --tags --abbrev=0)
git log "$PREV"..origin/main --oneline
```

If `PREV` is not the version users last received, set it to that tag explicitly.
Sort the commits into user-facing (CLI flags, environment variables, image behavior, translation or tagging output) and
internal (CI, tests, `tools/`, documentation).
Done when every commit in the range is in one of the two groups.

## 3. Pick the version

- `PATCH`: fixes only.
- `MINOR`: new, backwards-compatible behavior.
- `MAJOR`: anything that breaks a deployment, such as a renamed or removed environment variable.

Changes inside `tools/` never ship in the image, so they don't make a release major.
Done when you can name the change that justifies the chosen level.

## 4. Draft the notes

Group the user-facing changes under **What's New**, **Bug Fixes** and **Infrastructure**, with a short bold lead-in per
item and the PR number, for example `**Metric spoons**: converts tbsp to ml (#91)`.
End with `**Full Changelog**: https://github.com/lipkau/mealie_translate/compare/PREV...NEW`.
Done when the user has approved the version and the notes.

## 5. Tag and publish

```bash
git tag -a v1.2.3 -m "Release v1.2.3" origin/main
git push origin v1.2.3
gh release create v1.2.3 --title v1.2.3 --notes-file notes.md
```

Then check that CD published the version: `gh run list --workflow cd.yml --limit 1`.
Done when the CD run for the tag succeeded.
