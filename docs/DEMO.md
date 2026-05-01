# Demo Guide

The current demo uses synthetic seeded data for a Brazil Payments Launch. It is designed to show the core Track 1 story without requiring live Jira, Slack, GitHub, or Google Cloud credentials.

## Local Demo

```bash
python3 -m shipwright.demo
```

Expected output:

- one Dependency Gap finding
- one Slack-style dependency alert
- one Jira-style dependency comment
- one Flow-Based Standup Digest
- one Backlog Grooming Brief
- one generated Project Memory summary id

## HTTP Demo

```bash
python3 -m shipwright.server
```

Then open:

- `http://localhost:8080/healthz`
- `http://localhost:8080/demo`
- `http://localhost:8080/eval`

## Evaluation Harness

```bash
python3 -m unittest discover
```

The tests and evaluation harness cover:

- missing dependency detected
- signed-off dependency ignored
- duplicate alert suppression
- standup guardrails against productivity scoring
- stale backlog recommendation
- urgent CX defect surfacing
- MCP failure behavior

## Live Demo Target

The production demo should run the same behavior against:

- Jira sandbox project
- Slack demo workspace/channel
- GitHub demo repository
- Vertex AI Search-backed Project Memory
- Cloud Run-hosted runtime
