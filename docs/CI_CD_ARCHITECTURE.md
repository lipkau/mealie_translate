# CI/CD Pipeline Architecture

This project uses a separated CI/CD architecture with two distinct workflows for better performance, security, and maintainability.

## Architecture Overview

### 🔍 Continuous Integration (CI) - `.github/workflows/ci.yml`

**Purpose**: Validate code quality and functionality
**Triggers**: All pushes and pull requests
**Jobs**:

- **Markdown Linting**: Documentation quality checks (Node.js)
- **Code Quality & Security**: Linting and security scanning (Python 3.14)
- **Test Coverage**: Unit tests with coverage analysis (Python 3.14)
- **Test Matrix**: Compatibility tests across Python 3.11, 3.12, 3.13, 3.14
- **Docker Build Test**: Validates Docker image builds without publishing
- **Integration Tests**: Runs on main branch pushes and PRs with special label

**Optimization**: Separates coverage generation and quality checks from compatibility testing to avoid redundancy

### Continuous Deployment (CD) - `.github/workflows/cd.yml` + `_docker-build.yml`

**Purpose**: Build, publish, and deploy validated code
**Triggers**: Successful CI completion (via `workflow_run`)
**Jobs**:

- **gate**: Lightweight decision job -- determines which images to build (no Docker setup)
- **build-dev**: Builds `:dev` image (main push or version-tag release)
- **build-prod**: Builds `:v*` + `:latest` images (version-tag release)
- **build-pr**: Builds `:pr-<N>` image and comments on the PR

All build jobs call the reusable workflow `_docker-build.yml` which handles checkout, QEMU,
buildx, login, build-push, provenance attestation, and SBOM generation.
For version-tag releases, `build-dev` and `build-prod` run in parallel.

**Security**: Relies on separate Security pipeline for comprehensive vulnerability scanning after deployment

### PR Image Cleanup - `.github/workflows/pr-image-cleanup.yml`

**Purpose**: Delete ephemeral PR images from GHCR when a PR is closed
**Triggers**: `pull_request: closed`

### 🔒 Security Scanning - `.github/workflows/security.yml`

**Purpose**: Comprehensive security analysis of published artifacts
**Triggers**: After successful CD, weekly schedule, manual triggers
**Jobs**:

- **Python Security Scan**: Static code analysis and dependency vulnerability scanning
- **Docker Security Scan**: Container vulnerability scanning with Trivy (multiple image tags)
- **Security Summary**: Comprehensive reporting and notification

**Note**: This pipeline provides the primary security validation for the project, scanning both source code and
published container images

### 🤖 Dependabot Auto-merge - `.github/workflows/dependabot.yml`

**Purpose**: Automate dependency updates with safe auto-merge
**Triggers**: Dependabot pull requests (opened, synchronized, reopened)
**Behavior**:

- **Patch & Minor Updates**: Enables auto-merge for patch and minor-level dependency updates
- **Docker Updates**: Auto-merge for Docker base image patch and minor updates
- **GitHub Actions**: Auto-merge for GitHub Actions workflow updates
- **Manual Approval Required**: Due to GitHub security restrictions, auto-approval is not possible
- **Smart Comments**: Provides helpful context and commands for manual review

**Note**: While auto-merge is enabled, maintainer approval is still required due to GitHub's security policy that
prevents Actions from approving their own PRs.

## Benefits of Separation

### ⚡ Performance

- **Faster PR Feedback**: CI runs quickly without unnecessary Docker builds
- **Parallel Processing**: Testing and deployment can run independently
- **Resource Optimization**: Deployment resources only used when needed

### 🔒 Security

- **Separate Permissions**: CI has read-only access, CD has deployment permissions
- **Controlled Publishing**: Only validated code gets published
- **Environment Protection**: Production deployment requires manual approval

### 🔧 Maintainability

- **Clear Separation of Concerns**: Testing vs. deployment logic isolated
- **Easier Debugging**: Failures are easier to trace and fix
- **Flexible Triggers**: Different trigger conditions for different purposes

## Workflow Details

### CI Pipeline Triggers

```yaml
on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]
  workflow_dispatch:
```

A concurrency group keyed on `github.ref` cancels in-flight CI runs when new
commits are pushed rapidly to the same branch or PR.
This ensures only the latest commit's CI completes and triggers CD.

### CD Pipeline Triggers

CD is triggered exclusively by successful CI completion:

```yaml
on:
  workflow_run:
    workflows: ["Continuous Integration"]
    types: [completed]
```

A concurrency group keyed on the triggering branch cancels in-flight CD runs
as a defense-in-depth layer (CI concurrency is the primary guard).

## Integration Testing

Integration tests run conditionally:

- **Always** on main branch pushes
- **On PRs** only when labeled with `run-integration-tests`
- Uses environment variables for test configuration

## Docker Image Strategy

| Tag       | Built from                       | Dockerfile target | Purpose                    |
| --------- | -------------------------------- | ----------------- | -------------------------- |
| `dev`     | push to `main` / version tag    | development       | Beta users, staging        |
| `latest`  | version tag on `main`            | production        | Production deployments     |
| `v1.2.3`  | version tag on `main`            | production        | Pinned production version  |
| `pr-<N>`  | every PR (automatic)             | development       | Contributor testing        |

- **`dev`**: Always reflects the latest validated code on `main`.
  Also rebuilt during version-tag releases so it stays in sync with the release commit.
- **`latest`**: Points to the most recent stable release (version tags only).
- **`pr-<N>`**: Disposable image for testing a specific PR.
  Automatically deleted when the PR is closed.

See [Docker Image Strategy](DOCKER_IMAGE_STRATEGY.md) for the full decision matrix and build scenarios.

## Environment Configuration

### Staging Environment

- **Trigger**: Automatic on main branch
- **Protection Rules**: Optional approval required
- **Purpose**: Pre-production validation

### Production Environment

- **Trigger**: Manual on version tags
- **Protection Rules**: Required reviewers, deployment windows
- **Purpose**: Live application deployment

## GitHub Permissions

### CD Workflow Permissions

The Continuous Deployment workflow requires specific GitHub permissions to function properly:

#### CD workflow (all jobs inherit)

```yaml
permissions:
  contents: read       # Access repository code
  packages: write      # Push to GitHub Container Registry (GHCR)
  pull-requests: write # Comment on PRs with image tags
  id-token: write      # OIDC token for provenance attestation
```

#### `security-scan` job

```yaml
permissions:
  contents: read # Access repository code
  security-events: write # Upload security scan results to GitHub Security tab
  actions: read # Required for CodeQL integration
```

### Common Permission Issues

- **"installation not allowed to Create organization package"**: Missing `packages: write` permission
- **"Resource not accessible by integration"**: Missing `security-events: write` for SARIF uploads, or missing repository
  checkout, or GitHub Advanced Security not enabled on organization repositories
- **"The checkout path provided to the action does not appear to be a git repository"**: Missing `actions/checkout`
  step in security-scan job
- **403 Forbidden errors**: Insufficient token permissions for registry operations

### GitHub Advanced Security Requirements

For organization repositories, SARIF upload to GitHub Security tab requires:

- **GitHub Advanced Security** enabled for the organization/repository
- **Code scanning** features available (may require GitHub Enterprise or paid plan)
- Proper repository permissions in organization settings

If GitHub Advanced Security is not available:

- Security scans will still run and generate reports
- SARIF upload will fail gracefully with `continue-on-error: true`
- Vulnerability reports are available as workflow artifacts
- Consider using third-party security scanning tools as alternatives

### Best Practices

- Use minimal required permissions for each job
- CI workflows typically only need `contents: read`
- CD workflows need elevated permissions for deployments
- Security scanning requires `security-events: write` for integration with GitHub Security

## Usage Examples

### Running Integration Tests on PR

Add the `run-integration-tests` label to your pull request to trigger integration tests.

### Deploying to Staging

Push to main branch or merge a PR - staging deployment runs automatically after CI passes and uses the `:dev` image.

### Deploying to Production

Create and push a version tag to deploy stable releases to production:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will (in parallel):

1. Build and push production images with tags `v1.0.0` and `latest`
2. Build and push the `:dev` image so it stays in sync with the release

### Monitoring Deployments

- Check the Actions tab for workflow status
- Review environment deployment history
- Monitor security scan results in the Security tab

## Troubleshooting

### CI Failures

- Check test output in the test matrix job
- Review linting errors in the code quality checks
- Verify Docker build succeeds in docker-test job

### CD Failures

- Ensure CI completed successfully first
- Check Docker registry permissions
- Verify environment secrets are configured
- Review deployment logs in the appropriate environment job

## Future Enhancements

- **Automated Rollbacks**: Implement health checks and automatic rollback
- **Blue/Green Deployments**: Zero-downtime deployment strategy
- **Performance Testing**: Add performance benchmarks to CD pipeline
- **Multi-Environment**: Add development, QA, and UAT environments
