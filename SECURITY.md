# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.4.x   | :white_check_mark: |
| < 1.4   | :x:                |

## Reporting a Vulnerability

**DO NOT** create public GitHub issues for security vulnerabilities.

Instead, use one of the private channels below:

- GitHub private vulnerability reporting (preferred): <https://github.com/davidleconte/hcd-janusgraph/security/advisories/new>
- Repository owner contact (fallback): <https://github.com/davidleconte>

Include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

We will respond within 48 hours and provide regular updates.

## Security Measures

This project implements:

- ✅ No secrets in repository
- ✅ Environment-specific configurations
- ✅ Container image scanning
- ✅ Dependency vulnerability scanning
- ✅ Code security analysis (CodeQL)
- ✅ Secret scanning

## Best Practices

When contributing:

- Never commit `.env` files
- Use `.env.example` as template
- Rotate secrets after any accidental exposure
- Keep dependencies up to date
- Follow principle of least privilege
