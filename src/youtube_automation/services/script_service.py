"""Generate, correct, and independently review structured video plans."""

from __future__ import annotations

from typing import Sequence

from youtube_automation.exceptions import ProviderResponseError
from youtube_automation.models import ReviewResult, VideoPlan
from youtube_automation.providers.base import LLMProvider


class ScriptService:
    """Apply pipeline policy around an injected LLM provider."""

    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    def generate_and_review(
        self, topic: str, audience: str, sources: Sequence[str] = ()
    ) -> tuple[VideoPlan, ReviewResult]:
        """Generate a plan, retry malformed output once, and require approval."""
        try:
            plan = self.provider.generate_video_plan(topic, audience, sources)
        except ProviderResponseError as first_error:
            correction = (
                "The previous response was invalid. Regenerate the complete plan and correct "
                f"this validation problem: {first_error}"
            )
            plan = self.provider.generate_video_plan(topic, audience, sources, correction)

        review = self.provider.review_video_plan(plan)
        if not review.approved:
            details = "; ".join(review.issues) or review.summary
            raise ProviderResponseError(f"Video plan failed editorial review: {details}")
        return plan, review
