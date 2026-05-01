import os
import unittest

from shipwright.evaluation import build_seeded_coordinator, run_evaluations
from shipwright.mcp import MCP_TOOL_SCHEMAS

os.environ["SHIPWRIGHT_QUIET_LOGS"] = "1"


class ShipwrightTests(unittest.TestCase):
    def test_dependency_gap_posts_slack_and_jira_comment(self):
        coordinator = build_seeded_coordinator(missing_dependency=True)

        findings = coordinator.run_dependency_workflow("SHIP-100")

        self.assertEqual(len(findings), 1)
        self.assertIn("Payments/Compliance launch signoff", findings[0].summary)
        self.assertEqual(len(coordinator.mcp.slack_messages), 1)
        self.assertEqual(len(coordinator.mcp.issues["SHIP-100"].comments), 1)
        self.assertIn("Evidence Packet", coordinator.mcp.issues["SHIP-100"].comments[0])

    def test_signed_off_dependency_does_not_alert(self):
        coordinator = build_seeded_coordinator(missing_dependency=False)

        findings = coordinator.run_dependency_workflow("SHIP-100")

        self.assertEqual(findings, [])
        self.assertEqual(coordinator.mcp.slack_messages, [])

    def test_duplicate_alert_suppressed(self):
        coordinator = build_seeded_coordinator(missing_dependency=True)

        coordinator.run_dependency_workflow("SHIP-100")
        coordinator.run_dependency_workflow("SHIP-100")

        self.assertEqual(len(coordinator.mcp.slack_messages), 1)
        self.assertEqual(len(coordinator.mcp.issues["SHIP-100"].comments), 1)

    def test_standup_digest_guardrails(self):
        coordinator = build_seeded_coordinator()

        digest = coordinator.post_standup_digest()
        rendered = digest.render().lower()

        self.assertLessEqual(len(digest.needs_attention), 3)
        self.assertNotIn("productivity", rendered)
        self.assertNotIn("lazy", rendered)
        self.assertNotIn("inactive", rendered)
        self.assertNotIn("rank", rendered)

    def test_backlog_brief_recommends_without_mutating_jira(self):
        coordinator = build_seeded_coordinator()
        before_status = coordinator.mcp.issues["SHIP-140"].status

        brief = coordinator.post_backlog_brief()

        self.assertTrue(any("SHIP-140" in item for item in brief.stale_to_archive))
        self.assertTrue(any("SHIP-151" in item for item in brief.priority_changes))
        self.assertEqual(coordinator.mcp.issues["SHIP-140"].status, before_status)

    def test_mcp_tool_schemas_cover_required_systems(self):
        self.assertIn("jira.add_dependency_gap_comment", MCP_TOOL_SCHEMAS)
        self.assertIn("slack.post_dependency_alert", MCP_TOOL_SCHEMAS)
        self.assertIn("github.read_pull_requests", MCP_TOOL_SCHEMAS)

    def test_evaluation_harness_passes(self):
        results = run_evaluations()
        failures = [result for result in results if not result.passed]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
