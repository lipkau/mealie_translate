# Security Policy

## Supported Versions

We release patches for security vulnerabilities.
Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The Mealie Recipe Translator team and community take security bugs seriously.
We appreciate your efforts to responsibly disclose your findings, and will make every effort to
acknowledge your contributions.

To report a security issue, please use the GitHub Security Advisory
["Report a Vulnerability"](https://github.com/lipkau/mealie_translate/security/advisories/new) tab.

The team will send a response indicating the next steps in handling your report.
After the initial reply to your report, the security team will keep you informed of the progress
towards a fix and full announcement, and may ask for additional information or guidance.

## Security Considerations

### API Keys and Secrets

- **Never commit API keys, tokens, or secrets to the repository**
- Use the `.env` file for configuration (which is in `.gitignore`)
- Rotate your OpenAI and Mealie API keys regularly
- Use environment-specific API keys for development vs production

### Mealie Server Security

- Ensure your Mealie server is properly secured and updated
- Use strong authentication for your Mealie instance
- Limit API access to trusted networks when possible
- Monitor API usage for unusual patterns

### OpenAI API Security

- Use API keys with minimal required permissions
- Monitor your OpenAI usage for unexpected consumption
- Set usage limits and alerts in your OpenAI dashboard
- Never share API keys or include them in logs

### Docker Security

- Keep base images updated
- Use non-root users in production containers
- Scan images for vulnerabilities regularly
- Limit container privileges and network access

### Network Security

- Use HTTPS for all API communications
- Validate SSL certificates
- Consider using VPN or private networks for API access
- Implement proper firewall rules

## Best Practices

1. **Environment Isolation**: Keep development, staging, and production environments separate
2. **Access Control**: Limit access to production systems and API keys
3. **Monitoring**: Implement logging and monitoring for security events
4. **Updates**: Keep dependencies and base systems updated
5. **Backup**: Ensure secure backups of configurations and data

## Scope

This security policy applies to:

- The Mealie Recipe Translator application code
- Docker containers and deployment configurations
- Documentation and examples
- CI/CD pipelines

This policy does not cover:

- Third-party dependencies (report directly to their maintainers)
- Mealie server vulnerabilities (report to the Mealie project)
- OpenAI API vulnerabilities (report to OpenAI)

## Disclosure Policy

When the security team receives a security bug report, they will assign it to a primary handler.
This person will coordinate the fix and release process, involving the following steps:

- Confirm the problem and determine the affected versions.
- Audit code to find any potential similar problems.
- Prepare fixes for all releases still under maintenance.
- Release new versions as soon as possible.

## Comments on this Policy

If you have suggestions on how this process could be improved please submit a pull request.
