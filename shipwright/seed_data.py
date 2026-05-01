"""Seeded competition demo data."""

from __future__ import annotations

from shipwright.contracts import (
    JiraIssue,
    OwnershipRule,
    ProjectMemorySummary,
    PullRequest,
    TeamMember,
    TeamOwnershipMap,
)
from shipwright.mcp import SeededMcpGateway
from shipwright.memory import InMemoryProjectMemory


def team_members() -> tuple[TeamMember, ...]:
    return (
        TeamMember(
            id="user_001",
            name="Avery Chen",
            github="avery",
            jira="avery@example.com",
            slack="UAVERY",
            team="core-product",
        ),
        TeamMember(
            id="user_002",
            name="Mina Patel",
            github="mina",
            jira="mina@example.com",
            slack="UMINA",
            team="payments-compliance",
        ),
    )


def ownership_map() -> TeamOwnershipMap:
    return TeamOwnershipMap(
        rules=(
            OwnershipRule(
                id="intl-payments-compliance",
                trigger_terms=("brazil", "payments"),
                required_team="payments-compliance",
                required_signoff="Payments/Compliance launch signoff",
                source="Ownership docs: international payments require payments-compliance signoff.",
                slack_channel="#payments-compliance",
            ),
        )
    )


def project_memory() -> InMemoryProjectMemory:
    return InMemoryProjectMemory(
        summaries=[
            ProjectMemorySummary(
                id="brazil-launch-plan",
                title="Brazil Payments Launch Plan",
                body=(
                    "The Brazil launch includes localized checkout, payments, "
                    "tax handling, compliance review, and rollout coordination."
                ),
                sources=("launch-plan/brazil-payments.md",),
                updated_at="2026-05-01T12:00:00+00:00",
            ),
            ProjectMemorySummary(
                id="payments-ownership",
                title="Payments Compliance Ownership",
                body=(
                    "International payments work requires explicit signoff from "
                    "the payments-compliance team before launch readiness."
                ),
                sources=("ownership/service-catalog.md", "compliance/checklist.md"),
                updated_at="2026-05-01T12:00:00+00:00",
            ),
            ProjectMemorySummary(
                id="prior-phase-summary",
                title="Prior Checkout Phase Summary",
                body=(
                    "Checkout localization completed. Card processing changes were "
                    "deferred until payments-compliance confirms launch controls."
                ),
                sources=("memory/checkout-phase-summary.md",),
                updated_at="2026-05-01T12:00:00+00:00",
            ),
        ]
    )


def seeded_gateway(missing_dependency: bool = True) -> SeededMcpGateway:
    signoffs = () if missing_dependency else ("Payments/Compliance launch signoff",)
    linked = () if missing_dependency else ("SHIP-122",)
    issues = {
        "SHIP-100": JiraIssue(
            key="SHIP-100",
            title="Brazil payments launch",
            description=(
                "Launch Brazil payments with localized checkout, card handling, "
                "and compliance-ready rollout."
            ),
            status="In Progress",
            owner_team="core-product",
            labels=("launch", "brazil", "payments"),
            linked_issue_keys=linked,
            signoffs=signoffs,
            age_days=12,
            customer_impact="high",
        ),
        "SHIP-122": JiraIssue(
            key="SHIP-122",
            title="Payments compliance signoff for Brazil",
            description="Confirm payment controls and launch readiness.",
            status="Done",
            owner_team="payments-compliance",
            labels=("signoff", "payments"),
            signoffs=("Payments/Compliance launch signoff",),
            age_days=3,
            customer_impact="high",
        ),
        "SHIP-140": JiraIssue(
            key="SHIP-140",
            title="Year-old settings cleanup",
            description="Clean up legacy settings screen.",
            status="Backlog",
            owner_team="core-product",
            labels=("cleanup",),
            age_days=365,
            customer_impact="low",
        ),
        "SHIP-151": JiraIssue(
            key="SHIP-151",
            title="CX defect: failed card retry copy",
            description="Customers retrying failed cards see unclear messaging.",
            status="Backlog",
            owner_team="core-product",
            labels=("cx-defect", "payments"),
            age_days=5,
            customer_impact="high",
        ),
        "SHIP-152": JiraIssue(
            key="SHIP-152",
            title="CX defect duplicate: card retry error copy",
            description="Duplicate report for failed card retry messaging.",
            status="Backlog",
            owner_team="core-product",
            labels=("cx-defect", "duplicate", "payments"),
            linked_issue_keys=("SHIP-151",),
            age_days=4,
            customer_impact="medium",
        ),
    }
    prs = [
        PullRequest(
            number=238,
            title="Add Brazil checkout copy",
            author_user_id="user_001",
            status="merged",
            review_state="approved",
            ci_state="passing",
            age_days=1,
            linked_issue_key="SHIP-100",
        ),
        PullRequest(
            number=241,
            title="Payment retry UX fix",
            author_user_id="user_001",
            status="open",
            review_state="requested",
            ci_state="passing",
            age_days=4,
            linked_issue_key="SHIP-151",
        ),
    ]
    return SeededMcpGateway(issues=issues, pull_requests=prs)
