"""Domain contracts for Shipwright."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

JsonDict = dict[str, Any]
Impact = Literal["high", "medium", "low", "none"]
Platform = Literal["github", "jira", "linear", "slack"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class TeamMember:
    id: str
    name: str
    github: str
    jira: str
    slack: str
    team: str
    current_capacity: Literal["full", "partial", "unavailable"] = "full"


@dataclass(frozen=True)
class OwnershipRule:
    id: str
    trigger_terms: tuple[str, ...]
    required_team: str
    required_signoff: str
    source: str
    slack_channel: str

    def matches(self, text: str) -> bool:
        haystack = text.lower()
        return all(term.lower() in haystack for term in self.trigger_terms)


@dataclass(frozen=True)
class TeamOwnershipMap:
    rules: tuple[OwnershipRule, ...]

    def matching_rules(self, text: str) -> list[OwnershipRule]:
        return [rule for rule in self.rules if rule.matches(text)]


@dataclass(frozen=True)
class WorkEvent:
    user_id: str
    platform: Platform
    event_type: str
    entity_id: str
    context: str
    timestamp: str
    sprint_impact: Impact


@dataclass(frozen=True)
class ProjectMemorySummary:
    id: str
    title: str
    body: str
    sources: tuple[str, ...]
    updated_at: str


@dataclass(frozen=True)
class JiraIssue:
    key: str
    title: str
    description: str
    status: str
    owner_team: str | None = None
    labels: tuple[str, ...] = ()
    linked_issue_keys: tuple[str, ...] = ()
    signoffs: tuple[str, ...] = ()
    comments: tuple[str, ...] = ()
    age_days: int = 0
    customer_impact: Impact = "none"


@dataclass(frozen=True)
class PullRequest:
    number: int
    title: str
    author_user_id: str
    status: Literal["open", "merged", "closed"]
    review_state: Literal["none", "requested", "approved", "changes_requested"]
    ci_state: Literal["pending", "passing", "failing"]
    age_days: int
    linked_issue_key: str | None = None


@dataclass(frozen=True)
class EvidencePacket:
    source_launch_doc: str
    ownership_rule: str
    missing_evidence: tuple[str, ...]
    confidence: Literal["high", "medium", "low"]
    recommended_next_action: str
    supporting_sources: tuple[str, ...] = ()

    def render(self) -> str:
        missing = "; ".join(self.missing_evidence)
        sources = ", ".join(self.supporting_sources)
        return (
            f"Evidence Packet\n"
            f"- Launch source: {self.source_launch_doc}\n"
            f"- Ownership rule: {self.ownership_rule}\n"
            f"- Missing evidence: {missing}\n"
            f"- Confidence: {self.confidence}\n"
            f"- Recommended next action: {self.recommended_next_action}\n"
            f"- Supporting sources: {sources}"
        )


@dataclass(frozen=True)
class DependencyGapFinding:
    issue_key: str
    summary: str
    affected_team: str
    required_signoff: str
    evidence: EvidencePacket

    @property
    def dedupe_key(self) -> str:
        return f"dependency-gap:{self.issue_key}:{self.affected_team}:{self.required_signoff}"


@dataclass(frozen=True)
class StandupDigest:
    title: str
    shipped_yesterday: tuple[str, ...]
    in_flight: tuple[str, ...]
    needs_attention: tuple[str, ...]
    todays_focus: tuple[str, ...]

    def render(self) -> str:
        return _render_sections(
            self.title,
            {
                "SHIPPED YESTERDAY": self.shipped_yesterday,
                "IN FLIGHT": self.in_flight,
                "NEEDS ATTENTION": self.needs_attention,
                "TODAY'S FOCUS": self.todays_focus,
            },
        )


@dataclass(frozen=True)
class BacklogGroomingBrief:
    title: str
    priority_changes: tuple[str, ...]
    stale_to_archive: tuple[str, ...]
    duplicates_to_merge: tuple[str, ...]
    rationale: tuple[str, ...]

    def render(self) -> str:
        return _render_sections(
            self.title,
            {
                "PRIORITY CHANGES": self.priority_changes,
                "STALE TO ARCHIVE": self.stale_to_archive,
                "DUPLICATES TO MERGE": self.duplicates_to_merge,
                "RATIONALE": self.rationale,
            },
        )


@dataclass
class AlertDedupeRecord:
    key: str
    surfaced_at: str = field(default_factory=utc_now_iso)


def _render_sections(title: str, sections: dict[str, tuple[str, ...]]) -> str:
    lines = [title]
    for heading, items in sections.items():
        lines.append("")
        lines.append(heading)
        if not items:
            lines.append("- None")
        else:
            lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)
