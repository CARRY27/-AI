# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of DocAgent seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to [carry27@example.com](mailto:carry27@example.com) with the following information:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity (Critical: 7 days, High: 14 days, Medium: 30 days)

### Disclosure Policy

- We will confirm receipt of your vulnerability report
- We will investigate and validate the issue
- We will work on a fix and release timeline
- We will notify you when the issue is fixed
- We will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous)

## Security Best Practices for Deployment

### Environment Variables

- Never commit `.env` files with real credentials
- Use strong, unique passwords for all services
- Rotate API keys regularly

### Database Security

- Use encrypted connections (SSL/TLS)
- Implement proper access controls
- Regular backups with encryption

### Network Security

- Deploy behind a reverse proxy (nginx/traefik)
- Enable HTTPS with valid certificates
- Implement rate limiting
- Use firewall rules to restrict access

### Application Security

- Keep all dependencies updated
- Review Dependabot alerts regularly
- Enable audit logging
- Implement proper authentication and authorization

## Acknowledgments

We appreciate the security research community and will acknowledge researchers who responsibly disclose vulnerabilities.

Thank you for helping keep DocAgent and our users safe!
