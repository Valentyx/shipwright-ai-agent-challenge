# Roadmap

## Milestone 1: Public Scaffold

Status: complete.

- ADK-compatible root agent entrypoint.
- Seeded MCP gateway and minimal custom MCP server fallback.
- Domain contracts and core workflow services.
- Local demo, HTTP demo, and evaluation harness.
- Public-facing domain docs and ADR.

## Milestone 2: Live MCP Integration

- Run a 48-hour spike on community MCP servers for Jira, Slack, and GitHub.
- Keep any community server only if auth, Cloud Run deployment, tool schemas, and demo reliability are proven.
- Use minimal custom MCP servers for any connector that does not satisfy the demo contract.
- Add MCP contract tests around the live tool boundary.

## Milestone 3: Project Memory Grounding

- Create a small Vertex AI Search corpus with launch, ownership, service catalog, compliance, and phase-summary docs.
- Replace in-memory Project Memory with a Vertex-backed implementation.
- Ensure Dependency Gap alerts cite Project Memory evidence.

## Milestone 4: Cloud Run Demo

- Deploy the HTTP runtime to Cloud Run.
- Configure live MCP endpoints and Google Cloud credentials through environment variables or Secret Manager.
- Verify `/healthz`, `/demo`, and `/eval` remotely.
- Capture Cloud Logging traces for agent runs, MCP calls, and routed actions.

## Cut Line

Preserve:

- ADK + Gemini
- Cloud Run
- MCP-backed Jira/Slack/GitHub access
- Vertex AI Search grounding
- Dependency Gap workflow
- Slack + Jira autonomous action
- Evidence Packet
- Standup Digest
- Backlog Grooming Brief
- basic evaluation harness

Cut first:

- canned Slack Q&A
- nightly Project Memory generation
- Redis, replacing it with Postgres-backed or in-process demo dedupe
- extra visual polish
