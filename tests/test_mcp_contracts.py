import os
import unittest

from shipwright.mcp_live import McpClientConfig, ConnectorProbeResult, McpTool, _missing_required_tools, probe_all_from_env, probe_connector

os.environ["SHIPWRIGHT_QUIET_LOGS"] = "1"


class McpContractTests(unittest.TestCase):
    def test_unconfigured_connectors_report_clear_status(self):
        result = probe_connector(
            McpClientConfig(
                name="github",
                url="",
                required_tools=("github.read_pull_requests",),
            )
        )

        self.assertIsInstance(result, ConnectorProbeResult)
        self.assertFalse(result.passed)
        self.assertEqual(result.decision, "not configured; keep seeded fallback")
        self.assertEqual(result.missing_tools, ("github.read_pull_requests",))

    def test_configured_broken_connector_reports_error(self):
        result = probe_connector(
            McpClientConfig(
                name="jira",
                url="http://127.0.0.1:1",
                required_tools=("jira.read_launch_ticket",),
                timeout_seconds=0.1,
            )
        )

        self.assertFalse(result.passed)
        self.assertTrue(result.configured)
        self.assertEqual(result.missing_tools, ("jira.read_launch_ticket",))
        self.assertTrue(result.errors)
        self.assertEqual(result.decision, "custom fallback likely unless fixed during spike")

    def test_slack_send_message_capability_can_satisfy_shipwright_posts(self):
        config = McpClientConfig(
            name="slack",
            url="https://mcp.slack.com/mcp",
            required_tools=(
                "slack.post_dependency_alert",
                "slack.post_standup_digest",
                "slack.post_backlog_grooming_brief",
            ),
            tool_aliases={
                "slack.post_dependency_alert": ("send_message",),
                "slack.post_standup_digest": ("send_message",),
                "slack.post_backlog_grooming_brief": ("send_message",),
            },
        )

        missing = _missing_required_tools(
            config,
            [McpTool(name="send_message", description="Send message to any Slack conversation.")],
        )

        self.assertEqual(missing, ())

    def test_atlassian_rovo_tools_can_satisfy_jira_contract(self):
        config = McpClientConfig(
            name="jira",
            url="https://mcp.atlassian.com/v1/mcp/authv2",
            required_tools=(
                "jira.read_launch_ticket",
                "jira.read_linked_issues",
                "jira.read_sprint_backlog",
                "jira.add_dependency_gap_comment",
            ),
            tool_aliases={
                "jira.read_launch_ticket": ("getJiraIssue",),
                "jira.read_linked_issues": ("getJiraIssueRemoteIssueLinks", "searchJiraIssuesUsingJql"),
                "jira.read_sprint_backlog": ("searchJiraIssuesUsingJql",),
                "jira.add_dependency_gap_comment": ("addCommentToJiraIssue",),
            },
        )

        missing = _missing_required_tools(
            config,
            [
                McpTool(name="getJiraIssue", description="Get a Jira issue by ID or key."),
                McpTool(name="getJiraIssueRemoteIssueLinks", description="List remote issue links on a Jira issue."),
                McpTool(name="searchJiraIssuesUsingJql", description="Search Jira issues using JQL."),
                McpTool(name="addCommentToJiraIssue", description="Add a comment to a Jira issue."),
            ],
        )

        self.assertEqual(missing, ())

    def test_linear_tools_can_satisfy_tracker_contract(self):
        config = McpClientConfig(
            name="linear",
            url="https://mcp.linear.app/mcp",
            required_tools=(
                "linear.read_launch_issue",
                "linear.read_sprint_backlog",
                "linear.add_dependency_gap_comment",
            ),
            tool_aliases={
                "linear.read_launch_issue": ("issues",),
                "linear.read_sprint_backlog": ("issues",),
                "linear.add_dependency_gap_comment": ("comments",),
            },
        )

        missing = _missing_required_tools(
            config,
            [
                McpTool(name="issues", description="Find, create, and update Linear issues."),
                McpTool(name="comments", description="Find, create, and update Linear issue comments."),
            ],
        )

        self.assertEqual(missing, ())

    def test_live_connector_probe_skips_without_env(self):
        live_vars = (
            "SHIPWRIGHT_MCP_GITHUB_URL",
            "SHIPWRIGHT_MCP_SLACK_URL",
        )
        tracker_configured = bool(os.environ.get("SHIPWRIGHT_MCP_JIRA_URL") or os.environ.get("SHIPWRIGHT_MCP_LINEAR_URL"))
        if not all(os.environ.get(name) for name in live_vars) or not tracker_configured:
            self.skipTest("live MCP URLs are not configured")

        results = probe_all_from_env()
        failures = [result for result in results if not result.passed]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
