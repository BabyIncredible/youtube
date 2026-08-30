"""Protocols that decouple pipeline logic from paid provider SDKs."""

from __future__ import annotations

from typing import Protocol, Sequence

from youtube_automation.models import ReviewResult, VideoPlan


class LLMProvider(Protocol):
    """Generate a validated video plan from a topic and optional sources."""

    def generate_video_plan(
        self,
        topic: str,
        audience: str,
        sources: Sequence[str],
        correction: str | None = None,
    ) -> VideoPlan:
        """Return a complete validated plan for the requested topic."""
        ...

    def review_video_plan(self, plan: VideoPlan) -> ReviewResult:
        """Review a generated plan for factual, editorial, and safety issues."""
        ...
