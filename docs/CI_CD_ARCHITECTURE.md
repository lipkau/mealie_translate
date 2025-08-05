# CI/CD Pipeline Architecture

This project uses a separated CI/CD architecture with two distinct workflows for better performance, security, and maintainability.

## Architecture Overview

### 🔍 Continuous Integration (CI) - `.github/workflows/ci.yml`

**Purpose**: Validate code quality and functionality
**Triggers**: All pushes and pull requests
**Jobs**:

- **Test Matrix**: Python 3.11, 3.12, 3.13 with linting, type checking, and unit tests
- **Docker Build Test**: Validates Docker image builds without publishing
- **Integration Tests**: Runs on main branch pushes and PRs with special label

### 🚀 Continuous Deployment (CD) - `.github/workflows/cd.yml`

**Purpose**: Build, publish, and deploy validated code
**Triggers**: Main branch pushes, version tags, and successful CI completion
**Jobs**:

- **Docker Build & Push**: Creates and publishes container images
- **Security Scan**: Trivy vulnerability scanning with SARIF upload
- **Deploy Staging**: Automatic deployment to staging environment (main branch)
- **Deploy Production**: Manual deployment to production (version tags)

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
- **Purpose**: Testing and development environments

### Production Images

- **Tags**: `latest`, version tags (`v1.0.0`, `1.0`)
- **Target**: `production` stage
- **Purpose**: Production deployments

## Environment Configuration

### Staging Environment

- **Trigger**: Automatic on main branch
- **Protection Rules**: Optional approval required
- **Purpose**: Pre-production validation

### Production Environment

- **Trigger**: Manual on version tags
- **Protection Rules**: Required reviewers, deployment windows
- **Purpose**: Live application deployment

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

Push to main branch or merge a PR - staging deployment runs automatically after CI passes.

### Deploying to Production

Create and push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

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
