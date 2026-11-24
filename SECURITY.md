# Security Policy

## Reporting a vulnerability

Please **do not open a public issue**. Use GitHub's private reporting:
**Security tab > Report a vulnerability**. We aim to respond within 7 days.

## Supported versions

Only the latest released version receives security fixes.

## Principles

- Minimal dependencies. New dependencies need maintainer approval.
- No `eval`/`exec`/`pickle` on user-provided data.
- Releases are published through PyPI Trusted Publishing (no long-lived tokens).
