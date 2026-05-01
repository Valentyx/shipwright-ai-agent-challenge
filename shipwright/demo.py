"""Run the seeded Shipwright demo."""

from __future__ import annotations

from shipwright.evaluation import build_seeded_coordinator


def main() -> int:
    coordinator = build_seeded_coordinator(missing_dependency=True)
    result = coordinator.run_demo()
    print("Shipwright demo complete")
    print(f"Dependency findings: {len(result['dependency_findings'])}")
    print(f"Memory summary: {result['memory_summary_id']}")
    for kind, channel, message in coordinator.mcp.slack_messages:  # type: ignore[attr-defined]
        print("")
        print(f"[{kind}] {channel}")
        print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
