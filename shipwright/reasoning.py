"""Reasoning provider abstraction for Shipwright.

The provider is intentionally task-oriented. Shipwright services should ask for
specific domain reasoning outputs instead of depending on a generic chat API.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


DEFAULT_REASONING_PROVIDER = "deterministic"
DEFAULT_REASONING_MODEL = "gemini-2.5-flash"


@dataclass(frozen=True)
class ReasoningRequest:
    task_name: str
    facts: tuple[str, ...]
    source_ids: tuple[str, ...] = ()
    max_style: str = "concise"


@dataclass(frozen=True)
class ReasoningResult:
    text: str
    provider_name: str
    model_name: str
    estimated_input_tokens: int | None = None
    estimated_output_tokens: int | None = None
    estimated_cost_usd: float | None = None


class ReasoningProvider(Protocol):
    provider_name: str
    model_name: str

    def summarize_project_memory(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError

    def classify_coordination_signals(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError

    def explain_evidence(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError


@dataclass(frozen=True)
class DeterministicReasoningProvider:
    model_name: str = "deterministic-v1"
    provider_name: str = "deterministic"

    def summarize_project_memory(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            text=" ".join(request.facts),
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    def classify_coordination_signals(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            text="high-signal" if request.facts else "no-signal",
            provider_name=self.provider_name,
            model_name=self.model_name,
        )

    def explain_evidence(self, request: ReasoningRequest) -> ReasoningResult:
        source_text = f" Sources: {', '.join(request.source_ids)}." if request.source_ids else ""
        return ReasoningResult(
            text=f"{' '.join(request.facts)}{source_text}",
            provider_name=self.provider_name,
            model_name=self.model_name,
        )


@dataclass(frozen=True)
class GeminiReasoningProvider:
    """Managed Gemini provider placeholder.

    The first pass keeps live model calls out of unit tests and local seeded
    demos. Production wiring can implement these methods through Vertex AI or
    the Gemini API without changing service code.
    """

    model_name: str = DEFAULT_REASONING_MODEL
    provider_name: str = "gemini"

    def summarize_project_memory(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("GeminiReasoningProvider live calls are not wired yet.")

    def classify_coordination_signals(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("GeminiReasoningProvider live calls are not wired yet.")

    def explain_evidence(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("GeminiReasoningProvider live calls are not wired yet.")


@dataclass(frozen=True)
class LocalReasoningProvider:
    """Future self-served/local model provider placeholder."""

    model_name: str = "local-model"
    provider_name: str = "local"

    def summarize_project_memory(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("LocalReasoningProvider is reserved for future self-served model support.")

    def classify_coordination_signals(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("LocalReasoningProvider is reserved for future self-served model support.")

    def explain_evidence(self, request: ReasoningRequest) -> ReasoningResult:
        raise NotImplementedError("LocalReasoningProvider is reserved for future self-served model support.")


def configured_reasoning_model() -> str:
    return os.environ.get("SHIPWRIGHT_REASONING_MODEL", DEFAULT_REASONING_MODEL)


def reasoning_provider_from_env() -> ReasoningProvider:
    provider = os.environ.get("SHIPWRIGHT_REASONING_PROVIDER", DEFAULT_REASONING_PROVIDER).strip().lower()
    model = configured_reasoning_model()
    if provider == "deterministic":
        return DeterministicReasoningProvider()
    if provider == "gemini":
        return GeminiReasoningProvider(model_name=model)
    if provider == "local":
        return LocalReasoningProvider(model_name=model)
    raise ValueError(f"Unsupported SHIPWRIGHT_REASONING_PROVIDER: {provider}")
