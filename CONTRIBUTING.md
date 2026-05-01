# Contributing

Thanks for taking a look at Shipwright. This project is an early hackathon build, so the best contributions are focused, small, and easy to validate.

## Local Setup

Use Python 3.11 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The seeded demo does not require live Jira, Slack, GitHub, or Google Cloud credentials.

```bash
python3 -m shipwright.demo
python3 -m shipwright.server
```

## Checks

Run these before opening a PR:

```bash
python3 -m unittest discover
python3 -m py_compile agent.py shipwright/*.py tests/*.py
```

Live MCP checks are skipped unless the required environment variables are configured.

## Pull Requests

- Keep PRs focused on one behavior, integration, or documentation change.
- Do not commit `.env`, tokens, local ADK state, or generated caches.
- Include the checks you ran in the PR description.
- For live integrations, document whether credentials, scopes, or admin setup are required.

## Guardrails

Shipwright should not score individual productivity, infer laziness, rank people, or mutate backlog priority/status automatically.
