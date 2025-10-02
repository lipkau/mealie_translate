# Docker Image Strategy

This document explains when and how different Docker images are built in the Mealie Recipe Translator project.

## 🎯 Overview

Our Docker build strategy creates two types of images based on context:

- **Development Images**: For PR testing and development
- **Production Images**: For releases and production deployment

## 📦 Image Types

### Development Images (`target: development`)

- **Purpose**: Testing, development, and feature validation
- **Contents**: Application code + development tools and dependencies
- **Size**: Larger (includes dev dependencies)
- **Use Cases**: PR testing, feature branches, development environments

### Production Images (`target: production`)

- **Purpose**: Production deployment and stable releases
- **Contents**: Application code only with minimal dependencies
- **Size**: Smaller (optimized for production)
- **Use Cases**: Official releases, production deployments

## 🔄 Build Decision Matrix

| Scenario             | Branch | Tag Present | Image Built | Target      | Example Tag                                       |
| -------------------- | ------ | ----------- | ----------- | ----------- | ------------------------------------------------- |
| Development workflow | main   | ❌           | ❌           | -           | -                                                 |
| Feature testing      | PR     | ✅           | ✅           | development | `ghcr.io/lipkau/mealie_translate:pr-123-test-dev` |
| Production release   | main   | ✅           | ✅           | production  | `ghcr.io/lipkau/mealie_translate:v1.2.3`          |
| Regular PR           | PR     | ❌           | ❌           | -           | -                                                 |

## � Build Scenarios

### 1. **Development Workflow** (Main Branch)

```bash
git push origin main  # No tag
```

**Result**: No image built (CI runs, no CD)

**Use Cases**: Regular development, no deployment needed

### 2. **Feature Testing** (PR with Tag)

```bash
git tag pr-123-test
git push origin tag pr-123-test
```

**Result**: `ghcr.io/lipkau/mealie_translate:pr-123-test-dev` (development image)

**Use Cases**:

- PR reviewers can test specific features
- Integration testing with external services
- Feature validation before merge

### 3. **Production Release** (Main Branch + Tag)

```bash
git tag v1.2.3
git push origin tag v1.2.3
```

**Result**:

- `ghcr.io/lipkau/mealie_translate:v1.2.3` (production image)
- `ghcr.io/lipkau/mealie_translate:latest` (production image)

**Use Cases**:

- Official releases
- Production deployments
- Stable version distribution

### 4. **PR Without Tag** (Feature Branch)

```bash
git push origin feature-branch  # No tag
```

**Result**: No image built (CI only)

**Use Cases**: Regular development PRs that don't need testing

## 🏷️ Tagging Rules

### Git Tag Requirements

- **Format**: `v{major}.{minor}.{patch}[-suffix]`
- **Valid Examples**: `v1.0.0`, `v2.1.3-beta`, `pr-123-test`
- **Invalid Examples**: `1.0.0` (no v), `release-candidate` (no version)

### Docker Tag Sanitization

Git tags are automatically sanitized for Docker compatibility:

- Replace `/` with `-` (e.g., `feature/auth` → `feature-auth`)
- Replace `+` with `-` (e.g., `v1.0.0+build` → `v1.0.0-build`)
- Skip tags with spaces or invalid characters

## � Implementation Details

### Dockerfile Targets

```dockerfile
# Development target (includes dev dependencies)
FROM python:3.11-slim as development
RUN pip install --no-cache-dir -e .[dev]

# Production target (minimal dependencies)
FROM python:3.11-slim as production
RUN pip install --no-cache-dir .
```

### GitHub Actions Logic

```yaml
# Determine image type based on branch and tag
image_type: ${{ github.ref == 'refs/heads/main' && 'production' || 'development' }}

# Build with appropriate target
docker build --target ${{ steps.determine.outputs.image_type }}
```

## � Usage Examples

### Testing a Feature Branch

```bash
# Developer creates feature and tags for testing
git checkout feature-new-translator
git tag pr-456-translator-test
git push origin tag pr-456-translator-test

# Image built: ghcr.io/lipkau/mealie_translate:pr-456-translator-test-dev
# Reviewers can test: docker run ghcr.io/lipkau/mealie_translate:pr-456-translator-test-dev
```

### Creating a Release

```bash
# Maintainer creates production release
git checkout main
git tag v2.0.0
git push origin tag v2.0.0

# Images built:
#   - ghcr.io/lipkau/mealie_translate:v2.0.0
#   - ghcr.io/lipkau/mealie_translate:latest
```

## 🛠️ Troubleshooting

### Image Not Built

**Problem**: Tagged commit but no image appeared

**Solutions**:

1. Check if tag follows `v*` pattern for production images
2. Verify CI completed successfully before CD runs
3. Check GitHub Actions logs for build failures
4. Ensure tag was pushed: `git push origin tag <tagname>`

### Wrong Image Type

**Problem**: Expected production image but got development

**Solutions**:

1. Verify tag was pushed to `main` branch, not feature branch
2. Check if commit exists on main: `git branch --contains <tag>`
3. Re-tag on correct branch if needed

### Tag Sanitization Issues

**Problem**: Git tag contains invalid Docker characters

**Solutions**:

1. Use alphanumeric characters, hyphens, and underscores only
2. Avoid spaces, slashes (except in branch names), and special characters
3. Check CD workflow logs for sanitization details

## � Related Documentation

- [CI/CD Architecture](CI_CD_ARCHITECTURE.md): Complete pipeline overview
- [Development Guide](DEVELOPMENT.md): Local development setup
- [Docker Documentation](DOCKER.md): Container usage and deployment
