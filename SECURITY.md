# Security

Shipwright will eventually connect to Jira, Slack, GitHub, Linear, Google Cloud, and other systems that may contain sensitive company data. Please report security issues privately.

## Reporting a Vulnerability

Do not open a public issue for security reports.

Email: security@valentyx.com

Include:

- affected component or integration
- reproduction steps
- impact
- any relevant logs or screenshots with secrets removed

We will acknowledge reports as soon as practical and coordinate remediation privately.

## Secret Handling

- Never commit `.env` files, API tokens, OAuth secrets, session databases, or local ADK state.
- Use environment variables or a secret manager for live credentials.
- Keep demo data synthetic unless explicit permission exists to use real project data.
- Run public-readiness scans before publishing new docs or seeded data.

## Supported Versions

This project is pre-1.0 and built for a hackathon submission. Security fixes will target the default branch and active demo branches.
