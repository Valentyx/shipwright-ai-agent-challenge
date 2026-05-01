"""MCP-facing contracts and seeded gateway.

Agents depend on this gateway shape. Live implementations should satisfy these
methods through MCP tools; direct Jira/Slack/GitHub API clients belong only
inside MCP server implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Protocol

from shipwright.contracts import JiraIssue, PullRequest


MCP_TOOL_SCHEMAS = {
    "jira.read_launch_ticket": {
        "description": "Read the launch Jira issue by key.",
        "input": {"issue_key": "string"},
    },
    "jira.read_linked_issues": {
        "description": "Read Jira issues linked to a launch ticket.",
        "input": {"issue_key": "string"},
    },
    "jira.read_sprint_backlog": {
        "description": "Read sprint and backlog items for grooming.",
        "input": {"project_key": "string"},
    },
    "jira.add_dependency_gap_comment": {
        "description": "Add an evidence-backed dependency gap comment.",
        "input": {"issue_key": "string", "comment": "string"},
    },
    "slack.post_dependency_alert": {
        "description": "Post a targeted dependency gap alert.",
        "input": {"channel": "string", "message": "string"},
    },
    "slack.post_standup_digest": {
        "description": "Post a flow-based standup digest.",
        "input": {"channel": "string", "message": "string"},
    },
    "slack.post_backlog_grooming_brief": {
        "description": "Post a backlog grooming brief.",
        "input": {"channel": "string", "message": "string"},
    },
    "github.read_pull_requests": {
        "description": "Read PRs, review state, review lag, and CI state.",
        "input": {"repo": "string"},
    },
}


class McpGateway(Protocol):
    def read_launch_ticket(self, issue_key: str) -> JiraIssue:
        raise NotImplementedError

    def read_linked_issues(self, issue_key: str) -> list[JiraIssue]:
        raise NotImplementedError

    def read_sprint_backlog(self, project_key: str) -> list[JiraIssue]:
        raise NotImplementedError

    def add_dependency_gap_comment(self, issue_key: str, comment: str) -> None:
        raise NotImplementedError

    def post_dependency_alert(self, channel: str, message: str) -> None:
        raise NotImplementedError

    def post_standup_digest(self, channel: str, message: str) -> None:
        raise NotImplementedError

    def post_backlog_grooming_brief(self, channel: str, message: str) -> None:
        raise NotImplementedError

    def read_pull_requests(self, repo: str) -> list[PullRequest]:
        raise NotImplementedError


@dataclass
class SeededMcpGateway(McpGateway):
    """Local deterministic MCP gateway for demos and tests."""

    issues: dict[str, JiraIssue]
    pull_requests: list[PullRequest]
    slack_messages: list[tuple[str, str, str]] = field(default_factory=list)

    def read_launch_ticket(self, issue_key: str) -> JiraIssue:
        return self.issues[issue_key]

    def read_linked_issues(self, issue_key: str) -> list[JiraIssue]:
        issue = self.issues[issue_key]
        return [self.issues[key] for key in issue.linked_issue_keys]

    def read_sprint_backlog(self, project_key: str) -> list[JiraIssue]:
        return [issue for key, issue in self.issues.items() if key.startswith(project_key)]

    def add_dependency_gap_comment(self, issue_key: str, comment: str) -> None:
        issue = self.issues[issue_key]
        self.issues[issue_key] = replace(issue, comments=issue.comments + (comment,))

    def post_dependency_alert(self, channel: str, message: str) -> None:
        self.slack_messages.append(("dependency_alert", channel, message))

    def post_standup_digest(self, channel: str, message: str) -> None:
        self.slack_messages.append(("standup_digest", channel, message))

    def post_backlog_grooming_brief(self, channel: str, message: str) -> None:
        self.slack_messages.append(("backlog_grooming_brief", channel, message))

    def read_pull_requests(self, repo: str) -> list[PullRequest]:
        return list(self.pull_requests)
