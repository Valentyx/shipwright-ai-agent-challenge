"""Live MCP connector probing and gateway foundation.

This module intentionally keeps the live MCP layer small. It can probe generic
HTTP MCP endpoints, report capabilities, and adapt tool responses into
Shipwright contracts once a server satisfies the demo contract.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from shipwright.contracts import JiraIssue, PullRequest
from shipwright.mcp import MCP_TOOL_SCHEMAS, McpGateway


class McpConnectorError(RuntimeError):
    """Raised when a live MCP connector cannot satisfy a requested operation."""


@dataclass(frozen=True)
class McpClientConfig:
    name: str
    url: str
    auth_token: str = ""
    required_tools: tuple[str, ...] = ()
    tool_aliases: dict[str, tuple[str, ...]] = field(default_factory=dict)
    timeout_seconds: float = 10.0

    @property
    def configured(self) -> bool:
        return bool(self.url)


@dataclass(frozen=True)
class McpTool:
    name: str
    description: str = ""


@dataclass(frozen=True)
class ConnectorProbeResult:
    name: str
    configured: bool
    can_connect: bool
    can_list_tools: bool
    tool_count: int = 0
    required_tools: tuple[str, ...] = ()
    missing_tools: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return self.configured and self.can_connect and self.can_list_tools and not self.missing_tools and not self.errors

    @property
    def decision(self) -> str:
        if self.passed:
            return "candidate accepted for next live test"
        if not self.configured:
            return "not configured; keep seeded fallback"
        return "custom fallback likely unless fixed during spike"


class HttpMcpClient:
    """Minimal JSON-RPC-over-HTTP MCP client for capability probes."""

    def __init__(self, config: McpClientConfig):
        self.config = config
        self._request_id = 0

    def list_tools(self) -> list[McpTool]:
        payload = self._request("tools/list", {})
        tools = payload.get("tools") or payload.get("result", {}).get("tools") or []
        return [
            McpTool(name=str(tool.get("name", "")), description=str(tool.get("description", "")))
            for tool in tools
            if tool.get("name")
        ]

    def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        payload = self._request("tools/call", {"name": name, "arguments": arguments})
        if "content" in payload:
            return payload["content"]
        return payload.get("result", payload)

    def _request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self._request_id += 1
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self._request_id,
                "method": method,
                "params": params,
            }
        ).encode("utf-8")
        headers = {
            "content-type": "application/json",
            "accept": "application/json, text/event-stream",
        }
        if self.config.auth_token:
            headers["authorization"] = f"Bearer {self.config.auth_token}"
        request = urllib.request.Request(self.config.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            raise McpConnectorError(str(exc)) from exc
        return _decode_mcp_response(raw)


def _decode_mcp_response(raw: str) -> dict[str, Any]:
    """Decode JSON or simple SSE `data:` envelopes returned by MCP servers."""

    raw = raw.strip()
    if not raw:
        return {}
    if raw.startswith("data:"):
        for line in raw.splitlines():
            if line.startswith("data:"):
                raw = line.removeprefix("data:").strip()
                break
    parsed = json.loads(raw)
    if "error" in parsed:
        raise McpConnectorError(str(parsed["error"]))
    result = parsed.get("result", parsed)
    if not isinstance(result, dict):
        return {"result": result}
    return result


def probe_connector(config: McpClientConfig) -> ConnectorProbeResult:
    if not config.configured:
        return ConnectorProbeResult(
            name=config.name,
            configured=False,
            can_connect=False,
            can_list_tools=False,
            required_tools=config.required_tools,
            missing_tools=config.required_tools,
        )

    client = HttpMcpClient(config)
    try:
        tools = client.list_tools()
    except Exception as exc:  # noqa: BLE001 - probe should report connector failures, not crash.
        return ConnectorProbeResult(
            name=config.name,
            configured=True,
            can_connect=False,
            can_list_tools=False,
            required_tools=config.required_tools,
            missing_tools=config.required_tools,
            errors=(str(exc),),
        )

    missing = _missing_required_tools(config, tools)
    return ConnectorProbeResult(
        name=config.name,
        configured=True,
        can_connect=True,
        can_list_tools=True,
        tool_count=len(tools),
        required_tools=config.required_tools,
        missing_tools=missing,
    )


def connector_configs_from_env() -> dict[str, McpClientConfig]:
    return {
        "github": McpClientConfig(
            name="github",
            url=os.environ.get("SHIPWRIGHT_MCP_GITHUB_URL", ""),
            auth_token=os.environ.get("SHIPWRIGHT_MCP_GITHUB_TOKEN", os.environ.get("GITHUB_TOKEN", "")),
            required_tools=("github.read_pull_requests",),
        ),
        "jira": McpClientConfig(
            name="jira",
            url=os.environ.get("SHIPWRIGHT_MCP_JIRA_URL", ""),
            auth_token=os.environ.get("SHIPWRIGHT_MCP_JIRA_TOKEN", os.environ.get("JIRA_API_TOKEN", "")),
            required_tools=(
                "jira.read_launch_ticket",
                "jira.read_linked_issues",
                "jira.read_sprint_backlog",
                "jira.add_dependency_gap_comment",
            ),
            tool_aliases={
                "jira.read_launch_ticket": ("getJiraIssue",),
                "jira.read_linked_issues": (
                    "getJiraIssueRemoteIssueLinks",
                    "searchJiraIssuesUsingJql",
                    "getTeamworkGraphContext",
                ),
                "jira.read_sprint_backlog": ("searchJiraIssuesUsingJql",),
                "jira.add_dependency_gap_comment": ("addCommentToJiraIssue",),
            },
        ),
        "linear": McpClientConfig(
            name="linear",
            url=os.environ.get("SHIPWRIGHT_MCP_LINEAR_URL", ""),
            auth_token=os.environ.get("SHIPWRIGHT_MCP_LINEAR_TOKEN", os.environ.get("LINEAR_API_KEY", "")),
            required_tools=(
                "linear.read_launch_issue",
                "linear.read_sprint_backlog",
                "linear.add_dependency_gap_comment",
            ),
            tool_aliases={
                "linear.read_launch_issue": ("get_issue", "issue", "issues"),
                "linear.read_sprint_backlog": ("list_issues", "search_issues", "issues"),
                "linear.add_dependency_gap_comment": ("create_comment", "comment", "comments"),
            },
        ),
        "slack": McpClientConfig(
            name="slack",
            url=os.environ.get("SHIPWRIGHT_MCP_SLACK_URL", ""),
            auth_token=os.environ.get("SHIPWRIGHT_MCP_SLACK_TOKEN", os.environ.get("SLACK_BOT_TOKEN", "")),
            required_tools=(
                "slack.post_dependency_alert",
                "slack.post_standup_digest",
                "slack.post_backlog_grooming_brief",
            ),
            tool_aliases={
                "slack.post_dependency_alert": (
                    "slack.send_message",
                    "send_message",
                    "post_message",
                    "chat.postMessage",
                ),
                "slack.post_standup_digest": (
                    "slack.send_message",
                    "send_message",
                    "post_message",
                    "chat.postMessage",
                ),
                "slack.post_backlog_grooming_brief": (
                    "slack.send_message",
                    "send_message",
                    "post_message",
                    "chat.postMessage",
                ),
            },
        ),
    }


def probe_all_from_env() -> list[ConnectorProbeResult]:
    return [probe_connector(config) for config in connector_configs_from_env().values()]


def _missing_required_tools(config: McpClientConfig, tools: list[McpTool]) -> tuple[str, ...]:
    tool_names = {tool.name for tool in tools}
    searchable_tools = {f"{tool.name} {tool.description}".lower() for tool in tools}
    missing = []
    for required_tool in config.required_tools:
        aliases = (required_tool, *config.tool_aliases.get(required_tool, ()))
        if any(alias in tool_names for alias in aliases):
            continue
        if _capability_appears_in_descriptions(required_tool, aliases, searchable_tools):
            continue
        missing.append(required_tool)
    return tuple(missing)


def _capability_appears_in_descriptions(
    required_tool: str,
    aliases: tuple[str, ...],
    searchable_tools: set[str],
) -> bool:
    keywords = _capability_keywords(required_tool, aliases)
    return any(all(keyword in searchable_tool for keyword in keywords) for searchable_tool in searchable_tools)


def _capability_keywords(required_tool: str, aliases: tuple[str, ...]) -> tuple[str, ...]:
    if required_tool.startswith("slack.post_"):
        return ("send", "message")
    if required_tool.startswith("linear.read_"):
        return ("issue",)
    if required_tool == "linear.add_dependency_gap_comment":
        return ("comment",)
    if required_tool.startswith("github.read_"):
        return ("pull", "request")
    if required_tool == "jira.add_dependency_gap_comment":
        return ("comment",)
    if required_tool.startswith("jira.read_"):
        return ("issue",)
    parts = []
    for alias in aliases:
        parts.extend(alias.replace(".", "_").split("_"))
    return tuple(part for part in parts if len(part) > 2)


@dataclass
class LiveMcpGateway(McpGateway):
    """Gateway that maps Shipwright operations to configured MCP tool calls."""

    github: HttpMcpClient
    jira: HttpMcpClient
    slack: HttpMcpClient
    tool_names: dict[str, str] = field(default_factory=lambda: {name: name for name in MCP_TOOL_SCHEMAS})

    def read_launch_ticket(self, issue_key: str) -> JiraIssue:
        result = self.jira.call_tool(self.tool_names["jira.read_launch_ticket"], {"issue_key": issue_key})
        return _jira_issue_from_tool_result(result)

    def read_linked_issues(self, issue_key: str) -> list[JiraIssue]:
        result = self.jira.call_tool(self.tool_names["jira.read_linked_issues"], {"issue_key": issue_key})
        return [_jira_issue_from_tool_result(item) for item in _as_list(result)]

    def read_sprint_backlog(self, project_key: str) -> list[JiraIssue]:
        result = self.jira.call_tool(self.tool_names["jira.read_sprint_backlog"], {"project_key": project_key})
        return [_jira_issue_from_tool_result(item) for item in _as_list(result)]

    def add_dependency_gap_comment(self, issue_key: str, comment: str) -> None:
        self.jira.call_tool(
            self.tool_names["jira.add_dependency_gap_comment"],
            {"issue_key": issue_key, "comment": comment},
        )

    def post_dependency_alert(self, channel: str, message: str) -> None:
        self.slack.call_tool(self.tool_names["slack.post_dependency_alert"], {"channel": channel, "message": message})

    def post_standup_digest(self, channel: str, message: str) -> None:
        self.slack.call_tool(self.tool_names["slack.post_standup_digest"], {"channel": channel, "message": message})

    def post_backlog_grooming_brief(self, channel: str, message: str) -> None:
        self.slack.call_tool(
            self.tool_names["slack.post_backlog_grooming_brief"],
            {"channel": channel, "message": message},
        )

    def read_pull_requests(self, repo: str) -> list[PullRequest]:
        result = self.github.call_tool(self.tool_names["github.read_pull_requests"], {"repo": repo})
        return [_pull_request_from_tool_result(item) for item in _as_list(result)]


def _as_list(result: Any) -> list[Any]:
    if isinstance(result, list):
        return result
    if isinstance(result, dict):
        for key in ("issues", "pull_requests", "items", "result"):
            value = result.get(key)
            if isinstance(value, list):
                return value
    raise McpConnectorError(f"Expected list-like MCP result, got {type(result).__name__}")


def _jira_issue_from_tool_result(result: Any) -> JiraIssue:
    if isinstance(result, list):
        result = result[0] if result else {}
    if not isinstance(result, dict):
        raise McpConnectorError(f"Expected Jira issue dict, got {type(result).__name__}")
    return JiraIssue(
        key=str(result.get("key", "")),
        title=str(result.get("title") or result.get("summary") or ""),
        description=str(result.get("description", "")),
        status=str(result.get("status", "")),
        owner_team=result.get("owner_team"),
        labels=tuple(result.get("labels", ())),
        linked_issue_keys=tuple(result.get("linked_issue_keys", result.get("linkedIssues", ()))),
        signoffs=tuple(result.get("signoffs", ())),
        comments=tuple(result.get("comments", ())),
        age_days=int(result.get("age_days", result.get("ageDays", 0)) or 0),
        customer_impact=result.get("customer_impact", result.get("customerImpact", "none")),
    )


def _pull_request_from_tool_result(result: Any) -> PullRequest:
    if not isinstance(result, dict):
        raise McpConnectorError(f"Expected pull request dict, got {type(result).__name__}")
    return PullRequest(
        number=int(result.get("number", 0)),
        title=str(result.get("title", "")),
        author_user_id=str(result.get("author_user_id", result.get("author", ""))),
        status=result.get("status", result.get("state", "open")),
        review_state=result.get("review_state", result.get("reviewState", "none")),
        ci_state=result.get("ci_state", result.get("ciState", "pending")),
        age_days=int(result.get("age_days", result.get("ageDays", 0)) or 0),
        linked_issue_key=result.get("linked_issue_key", result.get("linkedIssueKey")),
    )
