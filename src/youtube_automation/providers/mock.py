"""Deterministic providers for local development without network credentials."""

from __future__ import annotations

from typing import Sequence

from youtube_automation.models import Scene, ThumbnailPlan, VideoPlan


class MockLLMProvider:
    """Create a repeatable, valid educational video plan."""

    def generate_video_plan(
        self, topic: str, audience: str, sources: Sequence[str]
    ) -> VideoPlan:
        """Return five distinct scenes suitable for exercising later stages."""
        source_urls = list(sources)
        scene_purposes = ["hook", "definition", "mechanism", "example", "summary"]
        scenes = [
            Scene(
                scene_id=index,
                narration=f"Scene {index} explains the {purpose} of {topic} in clear terms.",
                visual_type="generated_image",
                visual_prompt=f"Educational technical illustration for the {purpose} of {topic}, no logos",
                on_screen_text=purpose.title(),
                transition="fade",
                source_urls=source_urls,
            )
            for index, purpose in enumerate(scene_purposes, start=1)
        ]
        return VideoPlan(
            topic=topic,
            title=topic,
            description=f"A concise educational explanation of {topic} for {audience}.",
            audience=audience,
            hook=f"What actually happens when we use {topic}?",
            summary=f"A practical overview of {topic}.",
            tags=["education", "firmware", "embedded systems"],
            source_urls=source_urls,
            scenes=scenes,
            thumbnail=ThumbnailPlan(text="Firmware Made Clear", image_prompt=topic),
            contains_realistic_synthetic_media=False,
        )
