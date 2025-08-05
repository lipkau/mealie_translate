# CI/CD Pipeline Architecture

This project uses a separated CI/CD architecture with two distinct workflows for better performance, security, and maintainability.

## Architecture Overview

### 🔍 Continuous Integration (CI) - `.github/workflows/ci.yml`

**Purpose**: Validate code quality and functionality
**Triggers**: All pushes and pull requests
**Jobs**:

- **Markdown Linting**: Documentation quality checks (Node.js)
- **Code Quality & Security**: Linting and security scanning (Python 3.13)
- **Test Coverage**: Unit tests with coverage analysis (Python 3.13)
- **Test Matrix**: Compatibility tests across Python 3.11, 3.12, 3.13
- **Docker Build Test**: Validates Docker image builds without publishing
- **Integration Tests**: Runs on main branch pushes and PRs with special label

**Optimization**: Separates coverage generation and quality checks from compatibility testing to avoid redundancy

### 🚀 Continuous Deployment (CD) - `.github/workflows/cd.yml`

**Purpose**: Build, publish, and deploy validated code
**Triggers**: Main branch pushes, version tags, and successful CI completion
**Jobs**:

- **Docker Build & Push**: Creates and publishes container images
- **Deploy Staging**: Automatic deployment to staging environment (main branch)
- **Deploy Production**: Manual deployment to production (version tags)

**Security**: Relies on separate Security pipeline for comprehensive vulnerability scanning after deployment

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
    branches: [main, develop]
  pull_request:
    branches: [main, develop]
```

### CD Pipeline Triggers

```yaml
on:
  push:
    branches: [main] # Direct deployment
    tags: ["v*"] # Version releases
  workflow_run:
    workflows: ["Continuous Integration"]
    types: [completed]
    branches: [main] # After successful CI
```

## Integration Testing

Integration tests run conditionally:

- **Always** on main branch pushes
- **On PRs** only when labeled with `run-integration-tests`
- Uses environment variables for test configuration

## Docker Image Strategy

### Development Images

- **Tag**: `ghcr.io/owner/repo:dev`
- **Target**: `development` stage
- **Source**: Main branch pushes
- **Purpose**: Testing and staging environments

### Production Images

- **Tags**: `latest`, version tags (`v1.0.0`, `1.0`)
- **Target**: `production` stage
- **Source**: Version tag releases only
- **Purpose**: Production deployments

### Tagging Strategy

- **`dev`**: Built from main branch, contains latest development code
- **`latest`**: Points to the most recent stable release (version tags only)
- **Version tags**: Specific releases (`v1.0.0`, `1.0`) for precise deployment control
- **No `latest` on main**: Prevents accidental deployment of unstable code to production

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

#### `docker-build-and-push` job

```yaml
permissions:
  contents: read # Access repository code
  packages: write # Push to GitHub Container Registry (GHCR)
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

## Migration from Monolithic Pipeline

The old `ci-cd.yml` has been preserved as `ci-cd.yml.bak` for reference.
Key changes:

1. **Split Responsibilities**: Testing separated from deployment
2. **Conditional Logic**: Simpler, more predictable trigger conditions
3. **Enhanced Security**: Deployment permissions isolated
4. **Better Performance**: Reduced resource usage on PRs

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

This will:

1. Build and push production images with tags: `v1.0.0`, `1.0`, and `latest`
2. Deploy the `latest` tag to production (which points to `v1.0.0`)
3. Ensure production always runs stable, tagged releases

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
