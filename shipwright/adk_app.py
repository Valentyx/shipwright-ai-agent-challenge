"""ADK agent declarations for Shipwright."""

from dataclasses import dataclass

MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class LocalAgentSpec:
    """Fallback shape used when google-adk is not installed locally."""

    name: str
    model: str
    description: str
    instruction: str
    sub_agents: tuple["LocalAgentSpec", ...] = ()


def _local_agent(name: str, description: str, instruction: str) -> LocalAgentSpec:
    return LocalAgentSpec(
        model=MODEL,
        name=name,
        description=description,
        instruction=instruction,
    )


def create_root_agent():
    """Create the Shipwright ADK root agent, with a test-friendly fallback."""

    dependency_instruction = (
        "Detect Dependency Gaps: required external team involvement exists, "
        "but explicit ownership or signoff is absent. Use MCP-backed Jira, "
        "GitHub, and Slack tools; never call vendor APIs directly."
    )
    standup_instruction = (
        "Generate Flow-Based Standup Digests grouped by shipped work, in-flight "
        "work, risks, decisions, and needs-attention items. Never score people."
    )
    backlog_instruction = (
        "Create Backlog Grooming Briefs with recommendations only. Do not mutate "
        "Jira priority, status, or ownership."
    )
    memory_instruction = (
        "Maintain Project Memory: durable summaries of completed work, decisions, "
        "launches, and ownership knowledge. Index summaries for Vertex AI Search."
    )
    coordinator_instruction = (
        "You are Shipwright, a B2B autonomous coordination system. Coordinate "
        "specialist agents, route only high-signal findings, dedupe repeated "
        "alerts, and take the first routing action automatically through MCP "
        "tools: post Slack interventions and add Jira comments with Evidence "
        "Packets. Shipwright replaces the Scrum Master coordination function; "
        "it does not replace human judgment or monitor individual productivity."
    )

    try:
        from google.adk.agents.llm_agent import Agent
    except ModuleNotFoundError:
        dependency_agent = _local_agent(
            "dependency_agent",
            "Detects missing cross-team owner/signoff dependency gaps.",
            dependency_instruction,
        )
        standup_agent = _local_agent(
            "standup_agent",
            "Generates flow-based standup digests.",
            standup_instruction,
        )
        backlog_agent = _local_agent(
            "backlog_agent",
            "Produces backlog grooming recommendations.",
            backlog_instruction,
        )
        memory_agent = _local_agent(
            "memory_agent",
            "Maintains durable project memory summaries.",
            memory_instruction,
        )
        return LocalAgentSpec(
            model=MODEL,
            name="shipwright_coordinator",
            description="Coordinates Shipwright's specialist agents.",
            instruction=coordinator_instruction,
            sub_agents=(dependency_agent, standup_agent, backlog_agent, memory_agent),
        )

    dependency_agent = Agent(
        model=MODEL,
        name="dependency_agent",
        description="Detects missing cross-team owner/signoff dependency gaps.",
        instruction=dependency_instruction,
    )
    standup_agent = Agent(
        model=MODEL,
        name="standup_agent",
        description="Generates flow-based standup digests.",
        instruction=standup_instruction,
    )
    backlog_agent = Agent(
        model=MODEL,
        name="backlog_agent",
        description="Produces backlog grooming recommendations.",
        instruction=backlog_instruction,
    )
    memory_agent = Agent(
        model=MODEL,
        name="memory_agent",
        description="Maintains durable project memory summaries.",
        instruction=memory_instruction,
    )
    return Agent(
        model=MODEL,
        name="shipwright_coordinator",
        description="Coordinates Shipwright's specialist agents.",
        instruction=coordinator_instruction,
        sub_agents=[dependency_agent, standup_agent, backlog_agent, memory_agent],
    )
