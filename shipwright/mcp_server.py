"""Minimal custom MCP server fallback for the seeded demo.

Community MCP servers should be evaluated first. If one is unreliable for the
competition demo, this module exposes the narrow Jira/Slack/GitHub tool surface
Shipwright needs.
"""

from __future__ import annotations

from dataclasses import asdict

from shipwright.seed_data import seeded_gateway

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError as exc:  # pragma: no cover - optional cloud dependency
    raise SystemExit("Install the 'mcp' package to run this server.") from exc


mcp = FastMCP("shipwright-demo-tools")
gateway = seeded_gateway(missing_dependency=True)


@mcp.tool()
def jira_read_launch_ticket(issue_key: str) -> dict:
    """Read a launch Jira issue."""

    return asdict(gateway.read_launch_ticket(issue_key))


@mcp.tool()
def jira_read_linked_issues(issue_key: str) -> list[dict]:
    """Read Jira issues linked to a launch ticket."""

    return [asdict(issue) for issue in gateway.read_linked_issues(issue_key)]


@mcp.tool()
def jira_read_sprint_backlog(project_key: str) -> list[dict]:
    """Read sprint and backlog items."""

    return [asdict(issue) for issue in gateway.read_sprint_backlog(project_key)]


@mcp.tool()
def jira_add_dependency_gap_comment(issue_key: str, comment: str) -> dict:
    """Add an evidence-backed dependency gap comment."""

    gateway.add_dependency_gap_comment(issue_key, comment)
    return {"ok": True, "issue_key": issue_key}


@mcp.tool()
def slack_post_dependency_alert(channel: str, message: str) -> dict:
    """Post a targeted dependency gap alert."""

    gateway.post_dependency_alert(channel, message)
    return {"ok": True, "channel": channel}


@mcp.tool()
def slack_post_standup_digest(channel: str, message: str) -> dict:
    """Post a flow-based standup digest."""

    gateway.post_standup_digest(channel, message)
    return {"ok": True, "channel": channel}


@mcp.tool()
def slack_post_backlog_grooming_brief(channel: str, message: str) -> dict:
    """Post a backlog grooming brief."""

    gateway.post_backlog_grooming_brief(channel, message)
    return {"ok": True, "channel": channel}


@mcp.tool()
def github_read_pull_requests(repo: str) -> list[dict]:
    """Read PRs, review state, review lag, and CI state."""

    return [asdict(pr) for pr in gateway.read_pull_requests(repo)]


def main() -> int:
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
