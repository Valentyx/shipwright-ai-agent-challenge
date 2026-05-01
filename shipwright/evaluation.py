"""Simulation/evaluation harness for Shipwright."""

from __future__ import annotations

from dataclasses import dataclass

from shipwright.seed_data import ownership_map, project_memory, seeded_gateway
from shipwright.services import (
    BacklogAgent,
    DependencyAgent,
    InMemoryDedupeStore,
    MemoryAgent,
    ShipwrightCoordinator,
    StandupAgent,
)


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    detail: str


def build_seeded_coordinator(missing_dependency: bool = True) -> ShipwrightCoordinator:
    gateway = seeded_gateway(missing_dependency=missing_dependency)
    memory = project_memory()
    return ShipwrightCoordinator(
        dependency_agent=DependencyAgent(ownership_map(), memory, gateway),
        standup_agent=StandupAgent(gateway),
        backlog_agent=BacklogAgent(gateway),
        memory_agent=MemoryAgent(memory, gateway),
        mcp=gateway,
        dedupe=InMemoryDedupeStore(),
    )


def run_evaluations() -> list[EvalResult]:
    results: list[EvalResult] = []

    coordinator = build_seeded_coordinator(missing_dependency=True)
    findings = coordinator.run_dependency_workflow("SHIP-100")
    results.append(
        EvalResult(
            "missing dependency detected",
            bool(findings),
            f"{len(findings)} finding(s)",
        )
    )

    signed_off = build_seeded_coordinator(missing_dependency=False)
    no_findings = signed_off.run_dependency_workflow("SHIP-100")
    results.append(
        EvalResult(
            "signed-off dependency does not alert",
            not no_findings,
            f"{len(no_findings)} finding(s)",
        )
    )

    before = len(coordinator.mcp.slack_messages)  # type: ignore[attr-defined]
    coordinator.run_dependency_workflow("SHIP-100")
    after = len(coordinator.mcp.slack_messages)  # type: ignore[attr-defined]
    results.append(
        EvalResult(
            "duplicate alert suppressed",
            before == after,
            f"messages before={before}, after={after}",
        )
    )

    digest = coordinator.post_standup_digest()
    digest_text = digest.render().lower()
    forbidden = ("productivity", "lazy", "inactive", "rank")
    results.append(
        EvalResult(
            "standup avoids productivity scoring",
            not any(word in digest_text for word in forbidden),
            "checked forbidden surveillance language",
        )
    )
    results.append(
        EvalResult(
            "standup max three needs-attention items",
            len(digest.needs_attention) <= 3,
            f"{len(digest.needs_attention)} item(s)",
        )
    )

    brief = coordinator.post_backlog_brief()
    results.append(
        EvalResult(
            "stale backlog recommended for archive",
            any("SHIP-140" in item for item in brief.stale_to_archive),
            ", ".join(brief.stale_to_archive),
        )
    )
    results.append(
        EvalResult(
            "urgent CX defects surfaced",
            any("SHIP-151" in item for item in brief.priority_changes),
            ", ".join(brief.priority_changes),
        )
    )

    try:
        broken = build_seeded_coordinator(missing_dependency=True)
        broken.mcp.issues.pop("SHIP-100")  # type: ignore[attr-defined]
        broken.run_dependency_workflow("SHIP-100")
    except KeyError:
        results.append(EvalResult("MCP failure surfaces gracefully to caller", True, "missing issue raised KeyError"))
    else:
        results.append(EvalResult("MCP failure surfaces gracefully to caller", False, "no error raised"))

    return results
