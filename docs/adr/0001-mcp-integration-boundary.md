# MCP integration boundary

Shipwright agents call Jira, Slack, and GitHub through MCP-backed tools instead of direct vendor API clients. This keeps the Track 1 architecture aligned with the competition prompt, makes tool access auditable, and confines vendor-specific API details to MCP server implementations.
