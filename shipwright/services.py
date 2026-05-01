"""Shipwright domain workflows."""

from __future__ import annotations

from dataclasses import dataclass, field

from shipwright.contracts import (
    BacklogGroomingBrief,
    DependencyGapFinding,
    EvidencePacket,
    JiraIssue,
    ProjectMemorySummary,
    StandupDigest,
    TeamOwnershipMap,
    utc_now_iso,
)
from shipwright.mcp import McpGateway
from shipwright.memory import ProjectMemory
from shipwright.observability import record_event
from shipwright.reasoning import ReasoningProvider, ReasoningRequest, reasoning_provider_from_env


@dataclass
class InMemoryDedupeStore:
    seen: set[str] = field(default_factory=set)

    def first_seen(self, key: str) -> bool:
        if key in self.seen:
            return False
        self.seen.add(key)
        return True


@dataclass
class DependencyAgent:
    ownership: TeamOwnershipMap
    memory: ProjectMemory
    mcp: McpGateway

    def scan_launch(self, issue_key: str) -> list[DependencyGapFinding]:
        issue = self.mcp.read_launch_ticket(issue_key)
        context = f"{issue.title} {issue.description} {' '.join(issue.labels)}"
        findings: list[DependencyGapFinding] = []
        for rule in self.ownership.matching_rules(context):
            has_signoff = rule.required_signoff in issue.signoffs
            linked_issues = self.mcp.read_linked_issues(issue.key)
            has_linked_owner = any(link.owner_team == rule.required_team for link in linked_issues)
            if has_signoff and has_linked_owner:
                continue

            memory_hits = self.memory.query(f"{issue.title} {rule.required_team} {rule.required_signoff}")
            evidence = EvidencePacket(
                source_launch_doc=memory_hits[0].sources[0] if memory_hits else "Jira launch ticket",
                ownership_rule=rule.source,
                missing_evidence=(
                    f"No linked Jira issue owned by {rule.required_team}",
                    f"No explicit signoff named '{rule.required_signoff}'",
                ),
                confidence="high" if memory_hits else "medium",
                recommended_next_action=(
                    f"Ask {rule.required_team} to confirm owner and add "
                    f"'{rule.required_signoff}' before launch readiness."
                ),
                supporting_sources=tuple(source for hit in memory_hits for source in hit.sources),
            )
            findings.append(
                DependencyGapFinding(
                    issue_key=issue.key,
                    summary=(
                        f"{issue.title} requires {rule.required_signoff}, "
                        "but no owner/signoff is linked."
                    ),
                    affected_team=rule.required_team,
                    required_signoff=rule.required_signoff,
                    evidence=evidence,
                )
            )
        return findings


@dataclass
class StandupAgent:
    mcp: McpGateway

    def create_digest(self, project_key: str, repo: str) -> StandupDigest:
        backlog = self.mcp.read_sprint_backlog(project_key)
        prs = self.mcp.read_pull_requests(repo)
        shipped = tuple(
            f"{pr.title} (PR #{pr.number})"
            for pr in prs
            if pr.status == "merged"
        )
        in_flight = tuple(
            f"{pr.title} (PR #{pr.number}, review {pr.review_state}, CI {pr.ci_state})"
            for pr in prs
            if pr.status == "open"
        )
        attention = []
        for pr in prs:
            if pr.status == "open" and pr.age_days >= 3 and pr.review_state != "approved":
                attention.append(f"PR #{pr.number} has waited {pr.age_days} days for review.")
        for issue in backlog:
            if issue.customer_impact == "high" and "cx-defect" in issue.labels:
                attention.append(f"{issue.key} is a high-impact CX defect in the sprint backlog.")
        return StandupDigest(
            title="Shipwright Daily - Brazil Launch",
            shipped_yesterday=shipped,
            in_flight=in_flight,
            needs_attention=tuple(attention[:3]),
            todays_focus=(
                "Confirm Payments/Compliance signoff for Brazil launch.",
                "Resolve high-impact payment retry CX defect.",
            ),
        )


@dataclass
class BacklogAgent:
    mcp: McpGateway

    def create_grooming_brief(self, project_key: str) -> BacklogGroomingBrief:
        backlog = self.mcp.read_sprint_backlog(project_key)
        high_impact = tuple(
            f"{issue.key}: move up because customer impact is high."
            for issue in backlog
            if issue.customer_impact == "high" and issue.status == "Backlog"
        )
        stale = tuple(
            f"{issue.key}: archive candidate after {issue.age_days} days with low impact."
            for issue in backlog
            if issue.age_days >= 180 and issue.customer_impact in {"low", "none"}
        )
        duplicates = tuple(
            f"{issue.key}: merge into {issue.linked_issue_keys[0]}."
            for issue in backlog
            if "duplicate" in issue.labels and issue.linked_issue_keys
        )
        return BacklogGroomingBrief(
            title="Shipwright Backlog Grooming Brief - Brazil Launch",
            priority_changes=high_impact,
            stale_to_archive=stale,
            duplicates_to_merge=duplicates,
            rationale=(
                "Recommendations are based on customer impact, age, duplicate markers, and launch relevance.",
                "No Jira priority, status, or ownership changes were applied automatically.",
            ),
        )


@dataclass
class MemoryAgent:
    memory: ProjectMemory
    mcp: McpGateway
    reasoning: ReasoningProvider = field(default_factory=reasoning_provider_from_env)

    def create_nightly_summary(self, issue_key: str) -> str:
        issue = self.mcp.read_launch_ticket(issue_key)
        facts = (
            f"{issue.key} is {issue.status}.",
            f"Owner team is {issue.owner_team}.",
            f"Known signoffs: {', '.join(issue.signoffs) if issue.signoffs else 'none yet'}.",
        )
        result = self.reasoning.summarize_project_memory(
            ReasoningRequest(
                task_name="project_memory.nightly_summary",
                facts=facts,
                source_ids=(issue.key,),
                max_style="durable-summary",
            )
        )
        summary = ProjectMemorySummary(
            id=f"{issue.title.lower().replace(' ', '-')}-nightly-memory",
            title=f"{issue.title} nightly memory",
            body=result.text,
            sources=(issue.key,),
            updated_at=utc_now_iso(),
        )
        self.memory.index(summary)
        return summary.id


@dataclass
class ShipwrightCoordinator:
    dependency_agent: DependencyAgent
    standup_agent: StandupAgent
    backlog_agent: BacklogAgent
    memory_agent: MemoryAgent
    mcp: McpGateway
    dedupe: InMemoryDedupeStore = field(default_factory=InMemoryDedupeStore)

    def run_dependency_workflow(self, issue_key: str) -> list[DependencyGapFinding]:
        record_event("dependency_workflow.started", issue_key=issue_key)
        findings = self.dependency_agent.scan_launch(issue_key)
        for finding in findings:
            if not self.dedupe.first_seen(finding.dedupe_key):
                record_event("dependency_workflow.duplicate_suppressed", dedupe_key=finding.dedupe_key)
                continue
            message = self._render_dependency_alert(finding)
            self.mcp.post_dependency_alert("#payments-compliance", message)
            self.mcp.add_dependency_gap_comment(issue_key, message)
            record_event(
                "dependency_workflow.action_taken",
                issue_key=issue_key,
                affected_team=finding.affected_team,
                confidence=finding.evidence.confidence,
            )
        return findings

    def post_standup_digest(self, project_key: str = "SHIP", repo: str = "shipwright-demo") -> StandupDigest:
        digest = self.standup_agent.create_digest(project_key, repo)
        self.mcp.post_standup_digest("#eng-standup", digest.render())
        record_event("standup_digest.posted", project_key=project_key, needs_attention=len(digest.needs_attention))
        return digest

    def post_backlog_brief(self, project_key: str = "SHIP") -> BacklogGroomingBrief:
        brief = self.backlog_agent.create_grooming_brief(project_key)
        self.mcp.post_backlog_grooming_brief("#eng-planning", brief.render())
        record_event(
            "backlog_brief.posted",
            project_key=project_key,
            priority_changes=len(brief.priority_changes),
            stale_to_archive=len(brief.stale_to_archive),
        )
        return brief

    def run_demo(self) -> dict[str, object]:
        findings = self.run_dependency_workflow("SHIP-100")
        digest = self.post_standup_digest()
        brief = self.post_backlog_brief()
        memory_id = self.memory_agent.create_nightly_summary("SHIP-100")
        return {
            "dependency_findings": findings,
            "standup_digest": digest,
            "backlog_brief": brief,
            "memory_summary_id": memory_id,
        }

    @staticmethod
    def _render_dependency_alert(finding: DependencyGapFinding) -> str:
        return (
            f"Dependency Gap detected for {finding.issue_key}: {finding.summary}\n\n"
            f"{finding.evidence.render()}"
        )
