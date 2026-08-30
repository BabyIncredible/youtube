"""Protocols that decouple pipeline logic from paid provider SDKs."""

from __future__ import annotations

from typing import Protocol, Sequence

from youtube_automation.models import VideoPlan


class LLMProvider(Protocol):
    """Generate a validated video plan from a topic and optional sources."""

    def generate_video_plan(
        self, topic: str, audience: str, sources: Sequence[str]
    ) -> VideoPlan:
        """Return a complete validated plan for the requested topic."""
        ...
