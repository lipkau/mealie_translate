# GitHub Actions Artifacts Documentation

This document describes all artifacts uploaded by our GitHub Actions workflows and their retention policies.

## 📋 **Artifact Overview**

Our CI/CD pipelines capture comprehensive artifacts for debugging, compliance, and historical analysis.

## 🔄 **CI Pipeline Artifacts** (`ci.yml`)

### Test Results & Coverage

- **Artifact Name**: `test-results-python-{version}`
- **Contents**:
  - `pytest-results.xml` - JUnit test results for unit tests
  - `coverage.xml` - Coverage report (XML format)
  - `htmlcov/` - HTML coverage reports
- **Retention**: 30 days
- **Usage**: Debugging test failures, coverage analysis, CI dashboard integration
- **Features**:
  - Published to GitHub's test results UI via `dorny/test-reporter`
  - Compatible with IDE test result displays
  - Codecov integration for coverage tracking
- **Size**: ~1-5 MB per Python version

### Integration Test Results

- **Artifact Name**: `integration-test-results`
- **Contents**:
  - `pytest-results-integration.xml` - Integration test JUnit results
  - `test-logs/` - Integration test logs
- **Retention**: 14 days
- **Usage**: Debugging integration test failures
- **Features**:
  - Published to GitHub's test results UI via `dorny/test-reporter`
  - Separate from unit tests for clear reporting
- **Size**: ~1-10 MB

## 🚀 **CD Pipeline Artifacts** (`cd.yml`)

### Build Metadata

- **Artifact Name**: `build-metadata`
- **Contents**:
  - `build-metadata.txt` - Build information, git details, image tags
- **Retention**: 90 days
- **Usage**: Tracking builds, debugging deployments
- **Size**: ~1 KB

### Security Scan Results

- **Artifact Name**: `cd-security-scan`
- **Contents**:
  - `trivy-results.sarif` - Security scan results (SARIF format)
  - `trivy-report.json` - Detailed security report (JSON format)
- **Retention**: 90 days
- **Usage**: Security analysis, compliance auditing
- **Size**: ~100 KB - 5 MB

### Staging Deployment Logs

- **Artifact Name**: `staging-deployment-logs`
- **Contents**:
  - `staging-deployment.log` - Deployment timestamps and metadata
- **Retention**: 30 days
- **Usage**: Deployment tracking, troubleshooting
- **Size**: ~1 KB

### Production Deployment Logs

- **Artifact Name**: `production-deployment-logs`
- **Contents**:
  - `production-deployment.log` - Production deployment details
- **Retention**: 90 days
- **Usage**: Production deployment tracking, compliance
- **Size**: ~1 KB

## 🔒 **Security Pipeline Artifacts** (`security.yml`)

### Python Security Reports

- **Artifact Name**: `python-security-reports-{run_id}`
- **Contents**:
  - `bandit-report.json` - Static code analysis results
  - `pip-audit-report.json` - Dependency vulnerability scan
- **Retention**: 90 days
- **Usage**: Security auditing, vulnerability tracking
- **Size**: ~10-100 KB

### Docker Security Reports (per image)

- **Artifact Name**: `docker-security-reports-{tag}-{run_id}`
- **Contents**:
  - `trivy-results-{tag}.sarif` - Container vulnerability scan (SARIF)
  - `trivy-report-{tag}.json` - Detailed container security report
  - `trivy-table-{tag}.txt` - Human-readable vulnerability table
- **Retention**: 90 days
- **Usage**: Container security auditing, base image vulnerability tracking
- **Size**: ~100KB-1MB depending on vulnerabilities found

### Security Summary

- **Artifact Name**: `security-summary-{run_id}`
- **Contents**:
  - `security-summary.md` - Comprehensive security scan summary
- **Retention**: 90 days
- **Usage**: Executive summaries, quick security status overview
- **Size**: ~1-5 KB

## 📊 **Artifact Retention Strategy**

| Artifact Type         | Retention  | Reasoning                    |
| --------------------- | ---------- | ---------------------------- |
| **Test Results**      | 30 days    | Debugging recent failures    |
| **Integration Tests** | 14 days    | Shorter cycle, less critical |
| **Build Metadata**    | 90 days    | Deployment traceability      |
| **Security Reports**  | 90 days    | Compliance & auditing        |
| **Deployment Logs**   | 30-90 days | Production: longer retention |

## 🔍 **GitHub Security Integration**

### SARIF Uploads

All security scans upload SARIF files to GitHub's Security tab:

- **CD Pipeline**: Production image security scan
- **Security Pipeline**: Comprehensive multi-image scanning

### Security Advisories

- Automatic vulnerability detection
- Integration with Dependabot alerts
- Centralized security dashboard

## 📥 **Downloading Artifacts**

### Via GitHub UI

1. Navigate to workflow run
2. Scroll to "Artifacts" section
3. Click artifact name to download

### Via GitHub CLI

```bash
# List artifacts for a run
gh run view RUN_ID --repo OWNER/REPO

# Download specific artifact
gh run download RUN_ID --name ARTIFACT_NAME --repo OWNER/REPO

# Download all artifacts
gh run download RUN_ID --repo OWNER/REPO
```

### Via REST API

```bash
# List artifacts
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/runs/RUN_ID/artifacts

# Download artifact
curl -L -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/OWNER/REPO/actions/artifacts/ARTIFACT_ID/zip
```

## 🧹 **Artifact Management**

### Automatic Cleanup

- GitHub automatically deletes artifacts after retention period
- No manual cleanup required

### Storage Considerations

- **Average total size per workflow run**: ~10-50 MB
- **Monthly storage estimate**: ~1-5 GB (assuming daily runs)
- **Cost**: Included in GitHub Actions free tier for public repos

### Manual Cleanup (if needed)

```bash
# Delete old artifacts (requires admin permissions)
gh api repos/OWNER/REPO/actions/artifacts \
  --jq '.artifacts[] | select(.created_at < "2024-01-01") | .id' \
  | xargs -I {} gh api -X DELETE repos/OWNER/REPO/actions/artifacts/{}
```

## 🔧 **Troubleshooting Artifacts**

### Common Issues

**Artifact not found:**

- Check retention period (may have expired)
- Verify workflow completed successfully
- Check artifact name patterns

**Large artifact sizes:**

- Review HTML coverage reports (can be large)
- Consider compressing log files
- Implement artifact size limits

**Upload failures:**

- Check file paths exist
- Verify file permissions
- Review GitHub Actions logs

### Debug Commands

```bash
# Check artifact status in workflow
- name: Debug artifacts
  run: |
    find . -name "*.xml" -o -name "*.json" -o -name "*.log" | head -20
    ls -la htmlcov/ || echo "No htmlcov directory"
```

## 📈 **Artifact Analysis**

### Key Metrics to Track

- **Coverage trends** from coverage.xml files
- **Security vulnerabilities** from security reports
- **Test failure patterns** from pytest results
- **Build success rates** from build metadata

### Recommended Tooling

- **Coverage analysis**: Codecov integration
- **Security monitoring**: GitHub Security tab
- **Test analytics**: GitHub Actions insights
- **Custom dashboards**: Parse JSON artifacts with scripts

## 🔮 **Future Enhancements**

### Planned Improvements

- [ ] **Artifact compression** for large reports
- [ ] **Retention policies** based on branch/tag importance
- [ ] **Artifact indexing** for better searchability
- [ ] **Custom retention** for critical security scans
- [ ] **Artifact aggregation** across multiple runs

### Advanced Features

- [ ] **Artifact versioning** and comparison
- [ ] **Automated artifact analysis** with notifications
- [ ] **Integration** with external monitoring systems
- [ ] **Artifact-based deployment decisions**
