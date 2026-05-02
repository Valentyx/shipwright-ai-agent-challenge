# MCP Spike

This spike decides whether Shipwright can use official/community MCP servers for the live demo path or should fall back to minimal custom MCP servers for specific systems.

## Demo Contract

Shipwright agents need MCP tools for:

- Tracker: read launch issue, read linked issues/signoffs, read sprint backlog, add dependency-gap comment.
- Slack: post dependency alert, post standup digest, post backlog grooming brief.
- GitHub: read PRs, review state, CI state, review lag, and linked issue references.

## Candidate Servers

| System | Candidate | Auth | Status | Decision |
| --- | --- | --- | --- | --- |
| GitHub | Official GitHub MCP Server | `GITHUB_TOKEN` or remote auth | Pending | Evaluate first |
| Jira | Atlassian Rovo remote MCP Server | Atlassian OAuth/API access | Pending | Evaluate first |
| Linear | Linear remote MCP Server at `https://mcp.linear.app/mcp` | OAuth 2.1 or bearer token/API key | Pending | Evaluate as fastest tracker path |
| Slack | Slack MCP Server at `https://mcp.slack.com/mcp` | confidential OAuth with Slack app identity | Pending | Evaluate first |

## Tracker-Specific Notes

Jira remains the primary enterprise positioning target. Atlassian Rovo MCP is powerful and supports the Jira actions Shipwright needs, but it has the highest admin/auth risk. It uses `https://mcp.atlassian.com/v1/mcp/authv2`, normally with OAuth 2.1, and API-token auth only works when enabled by the organization admin.

Shipwright's Jira contract maps to Atlassian tools as:

- `jira.read_launch_ticket` -> `getJiraIssue`
- `jira.read_linked_issues` -> `getJiraIssueRemoteIssueLinks`, `searchJiraIssuesUsingJql`, or `getTeamworkGraphContext`
- `jira.read_sprint_backlog` -> `searchJiraIssuesUsingJql`
- `jira.add_dependency_gap_comment` -> `addCommentToJiraIssue`

Linear is a strong optional live tracker path because its official remote MCP server supports Streamable HTTP at `https://mcp.linear.app/mcp`, OAuth 2.1 with dynamic client registration, and bearer-token/API-key auth for server use. If Jira admin setup becomes slow, use Linear to prove the live tracker MCP path while preserving Jira as the enterprise target.

## Slack-Specific Notes

Slack's official MCP server uses JSON-RPC 2.0 over Streamable HTTP at `https://mcp.slack.com/mcp`. Slack does not support SSE-based connections or Dynamic Client Registration for this path at this time.

The Shipwright spike should treat Slack as a first-class official MCP target, but the probe must evaluate capabilities rather than expecting Shipwright's internal tool names to appear verbatim. Shipwright needs the Slack MCP server to provide at least a send-message capability that can cover dependency alerts, standup digests, and backlog grooming briefs.

Slack MCP clients must be backed by a registered Slack app with a fixed app ID. Only directory-published apps or internal apps may use MCP. For the demo, use an internal Slack app if the workspace allows it.

Minimum Slack scope for the Shipwright demo path:

- `chat:write` for posting dependency alerts, standup digests, and backlog briefs.

Useful later scopes if Slack becomes part of Project Memory or Q&A:

- channel/thread history scopes for reading project channels
- search scopes for searching messages/files/channels/users
- user read scopes for identity resolution

## Probe Command

Set only placeholder-free local values in `.env` or your shell. Never commit real secrets.

```bash
python3 -m shipwright.mcp_probe
```

The probe checks whether each configured connector can list tools and whether the required Shipwright tool names are present. By default the command is informational and exits successfully even when connectors are not configured. Use strict mode when you want connector readiness to fail the command:

```bash
SHIPWRIGHT_MCP_STRICT=1 python3 -m shipwright.mcp_probe
```

A failed probe does not fail the local seeded demo; it means the connector needs mapping, configuration, or a custom fallback.

## Required Environment

- `SHIPWRIGHT_MCP_GITHUB_URL`
- `SHIPWRIGHT_MCP_GITHUB_TOKEN` or `GITHUB_TOKEN`
- `SHIPWRIGHT_MCP_JIRA_URL`
- `SHIPWRIGHT_MCP_JIRA_TOKEN` or `JIRA_API_TOKEN`
- `SHIPWRIGHT_MCP_LINEAR_URL`
- `SHIPWRIGHT_MCP_LINEAR_TOKEN` or `LINEAR_API_KEY`
- `SHIPWRIGHT_MCP_SLACK_URL`
- `SHIPWRIGHT_MCP_SLACK_TOKEN`, `SLACK_MCP_USER_TOKEN`, or `SLACK_BOT_TOKEN`
- `SLACK_MCP_APP_ID`
- `SLACK_MCP_CLIENT_ID`
- `SLACK_MCP_CLIENT_SECRET`

## Fallback Rule

Use an official/community server only if it satisfies the exact demo contract and can plausibly run from the Cloud Run architecture. If auth, deployment, schema, or reliability blocks the spike, implement a minimal custom MCP server for that system while keeping agents behind the same MCP boundary.

## Sources

- GitHub MCP Server: https://github.com/github/github-mcp-server
- Atlassian Rovo MCP Server: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/getting-started-with-the-atlassian-remote-mcp-server/
- Atlassian Rovo supported tools: https://support.atlassian.com/atlassian-rovo-mcp-server/docs/supported-tools/
- Linear MCP Server: https://linear.app/docs/mcp
- Slack MCP Server: https://slack.com/help/articles/48855576908307-Guide-to-the-Slack-MCP-server
- Slack MCP Developer Docs: https://docs.slack.dev/ai/slack-mcp-server/
- ADK MCP tools: https://google.github.io/adk-docs/tools-custom/mcp-tools/
