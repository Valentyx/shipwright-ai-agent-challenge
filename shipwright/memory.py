"""Project Memory retrieval and summarization."""

from __future__ import annotations

from dataclasses import dataclass

from shipwright.contracts import ProjectMemorySummary, utc_now_iso


class ProjectMemory:
    """Searchable durable project knowledge.

    The demo implementation is in-memory. Production wiring should back this
    interface with Vertex AI Search.
    """

    def query(self, query: str, limit: int = 5) -> list[ProjectMemorySummary]:
        raise NotImplementedError

    def index(self, summary: ProjectMemorySummary) -> None:
        raise NotImplementedError


@dataclass
class InMemoryProjectMemory(ProjectMemory):
    summaries: list[ProjectMemorySummary]

    def query(self, query: str, limit: int = 5) -> list[ProjectMemorySummary]:
        terms = {term.lower() for term in query.split() if len(term) > 2}
        scored: list[tuple[int, ProjectMemorySummary]] = []
        for summary in self.summaries:
            haystack = f"{summary.title} {summary.body}".lower()
            score = sum(1 for term in terms if term in haystack)
            if score:
                scored.append((score, summary))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [summary for _, summary in scored[:limit]]

    def index(self, summary: ProjectMemorySummary) -> None:
        self.summaries.append(summary)


def summarize_completed_work(title: str, facts: list[str], sources: list[str]) -> ProjectMemorySummary:
    """Create a durable memory summary from stable, completed-work facts."""

    body = " ".join(facts)
    return ProjectMemorySummary(
        id=title.lower().replace(" ", "-"),
        title=title,
        body=body,
        sources=tuple(sources),
        updated_at=utc_now_iso(),
    )
