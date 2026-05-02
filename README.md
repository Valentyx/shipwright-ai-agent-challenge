# Shipwright Agent

Shipwright is an autonomous multi-agent system that replaces the Scrum Master coordination function by continuously monitoring engineering flow, detecting dependency gaps, and routing the first action automatically.

Repository: https://github.com/Valentyx/shipwright-ai-agent-challenge

## Status

This repository is an early competition scaffold. The current implementation uses synthetic demo data and a seeded MCP gateway so the core product behavior can be tested locally. Live Jira, Slack, GitHub, Vertex AI Search, and Cloud Run wiring are the next milestones.

Shipwright is an independent hackathon project. It is not affiliated with or endorsed by Google, Atlassian/Jira, Slack, GitHub, or their parent companies.

## Competition Shape

- Track: Google for Startups AI Agents Challenge, Track 1 Build
- Runtime: ADK + Gemini on Cloud Run
- Integration boundary: ADK agents call MCP tools for Jira/Linear, Slack, and GitHub
- Grounding: Project Memory is designed to be backed by Vertex AI Search
- Demo: Brazil Payments Launch dependency gap, Slack intervention, Jira comment, standup digest, backlog grooming brief

## Local Demo

The local demo uses seeded MCP gateway data so the core behavior can be tested without live Jira, Slack, GitHub, or Google Cloud credentials.

```bash
python3 -m shipwright.demo
python3 -m shipwright.server
```

Then visit:

- `http://localhost:8080/healthz`
- `http://localhost:8080/demo`
- `http://localhost:8080/eval`

## Tests

```bash
python3 -m unittest discover
```

The tests cover Dependency Gap detection, Evidence Packet generation, Slack/Jira actions, duplicate suppression, standup guardrails, backlog recommendations, and the seeded evaluation harness.

## Cloud Run

This repo includes a minimal Cloud Run-compatible HTTP server:

```bash
docker build -t shipwright-agent .
docker run -p 8080:8080 shipwright-agent
```

For ADK-native deployment after installing `google-adk`, use the ADK Cloud Run deployment flow against this package and configure live MCP servers for Jira, Slack, GitHub, plus Vertex AI Search for Project Memory.

## MCP

The production goal is to use reliable community MCP servers where they satisfy the demo contract. If they do not, this repo includes a minimal custom fallback server:

```bash
python3 -m shipwright.mcp_server
```

To probe live MCP endpoints for the current spike:

```bash
python3 -m shipwright.mcp_probe
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Demo Guide](docs/DEMO.md)
- [MCP Spike](docs/MCP_SPIKE.md)
- [Roadmap](docs/ROADMAP.md)
- [Domain Context](CONTEXT.md)
- [Architecture Decisions](docs/adr/0001-mcp-integration-boundary.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)

## Guardrails

- No productivity scoring
- No laziness or inactivity inference
- No person ranking
- Mention individuals only when action is genuinely required
- Backlog grooming produces recommendations only; it does not mutate Jira priority, status, or ownership
