# Shipwright

Shipwright is a B2B autonomous coordination system for engineering teams. It replaces the Scrum Master coordination function by detecting coordination gaps, grounding decisions in project memory, and routing the first action automatically.

## Language

**Dependency Gap**:
A required external team involvement exists, but explicit ownership or signoff is absent.
_Avoid_: blocker, risk, dependency issue

**Team Ownership Map**:
Required v1 configuration that maps domains, services, components, and approval requirements to owning teams.
_Avoid_: team config, routing config

**Project Memory**:
Durable summaries of completed work, decisions, launches, and ownership knowledge.
_Avoid_: raw ticket history, event log

**Evidence Packet**:
A compact, auditable explanation of sources, missing evidence, confidence, and recommended next action.
_Avoid_: explanation, reason blob

**Flow-Based Standup Digest**:
A daily digest organized by shipped work, in-flight work, risks, decisions, and attention items.
_Avoid_: person-by-person status, productivity report

**Backlog Grooming Brief**:
A recommendation brief for priority changes, stale tickets, duplicates, and rationale.
_Avoid_: auto-prioritization, backlog mutation

**Coordination Function**:
Ceremony prep, dependency surfacing, and flow alignment normally handled by a Scrum Master.
_Avoid_: Scrum Master replacement as a person

## Relationships

- A **Team Ownership Map** defines when a **Dependency Gap** can exist.
- A **Dependency Gap** produces an **Evidence Packet**.
- A **Project Memory** result can support an **Evidence Packet**.
- A **Flow-Based Standup Digest** may mention an individual only when action is required.
- A **Backlog Grooming Brief** recommends changes but does not mutate tracker state.
- The **Coordination Function** is automated through Slack alerts, Jira comments, digests, and briefs.

## Example Dialogue

> **Dev:** "The Brazil payments launch has Jira activity and merged PRs. Is it ready?"
> **Domain expert:** "Not unless the **Team Ownership Map** requirement for Payments/Compliance signoff is satisfied."
> **Dev:** "So if no linked owner or signoff exists, Shipwright raises a **Dependency Gap**?"
> **Domain expert:** "Yes, and the alert must include an **Evidence Packet** so the team can audit why Shipwright acted."

## Flagged Ambiguities

- "Replace Scrum Master" means replace the **Coordination Function**, not remove human judgment or monitor individual productivity.
- "Memory" means **Project Memory**, not raw transient ticket noise.
