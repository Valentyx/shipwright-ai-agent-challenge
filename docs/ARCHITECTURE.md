# Architecture

Shipwright is a Google ADK multi-agent system that coordinates engineering flow through MCP-backed tools and grounded project memory.

## Runtime

- **ADK + Gemini**: agent orchestration and reasoning.
- **Cloud Run**: deployable HTTP runtime for the demo service.
- **MCP**: integration boundary for Jira, Slack, and GitHub.
- **Vertex AI Search**: planned backing store for Project Memory grounding.
- **Postgres / Redis**: future durable state and short-lived dedupe/lock storage.

## Agents

- **Coordinator Agent**: routes workflows, suppresses duplicate alerts, and triggers visible actions.
- **Dependency Agent**: detects missing cross-team owner/signoff dependency gaps.
- **Standup Agent**: generates flow-based standup digests.
- **Backlog Agent**: produces grooming recommendations without mutating Jira state.
- **Memory Agent**: creates durable Project Memory summaries and indexes them for retrieval.

## Integration Boundary

Agents should call Jira, Slack, and GitHub through MCP tools. Direct vendor API clients belong inside MCP server implementations only.

Current local development uses a seeded MCP gateway so the product behavior can be tested without live credentials. The live path will replace that gateway with community MCP servers or minimal custom MCP servers that satisfy the same tool contracts.

## Demo Flow

1. Project Memory retrieves launch, ownership, service catalog, and compliance evidence.
2. Dependency Agent compares retrieved evidence with current Jira/GitHub state.
3. Coordinator dedupes the finding and routes it.
4. Slack receives a targeted dependency alert.
5. Jira receives a comment containing the same Evidence Packet.
6. Standup and backlog agents post supporting ceremony-replacement outputs.
