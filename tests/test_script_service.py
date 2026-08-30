"""Tests for plan correction and independent editorial review policy."""

from typing import Sequence

import pytest

from youtube_automation.exceptions import ProviderResponseError
from youtube_automation.models import ReviewResult, VideoPlan
from youtube_automation.providers.mock import MockLLMProvider
from youtube_automation.services.script_service import ScriptService


class CorrectingProvider:
    """Fail once, then return a valid plan for correction-policy testing."""

    def __init__(self) -> None:
        self.corrections: list[str | None] = []
        self.plan = MockLLMProvider().generate_video_plan("Secure Boot", "learners", ())

    def generate_video_plan(
        self,
        topic: str,
        audience: str,
        sources: Sequence[str],
        correction: str | None = None,
    ) -> VideoPlan:
        self.corrections.append(correction)
        if len(self.corrections) == 1:
            raise ProviderResponseError("scene IDs were not sequential")
        return self.plan

    def review_video_plan(self, plan: VideoPlan) -> ReviewResult:
        return ReviewResult(approved=True, issues=[], summary="Approved after correction.")


class RejectingProvider(MockLLMProvider):
    """Return a valid plan that fails the independent review gate."""

    def review_video_plan(self, plan: VideoPlan) -> ReviewResult:
        return ReviewResult(
            approved=False,
            issues=["Unsupported factual claim"],
            summary="Revision required.",
        )


def test_invalid_plan_is_regenerated_once_with_correction() -> None:
    provider = CorrectingProvider()

    plan, review = ScriptService(provider).generate_and_review("Secure Boot", "learners")

    assert plan == provider.plan
    assert review.approved is True
    assert provider.corrections[0] is None
    assert "scene IDs were not sequential" in (provider.corrections[1] or "")
    assert len(provider.corrections) == 2


def test_unapproved_review_stops_the_pipeline() -> None:
    with pytest.raises(ProviderResponseError, match="Unsupported factual claim"):
        ScriptService(RejectingProvider()).generate_and_review("Secure Boot", "learners")


def test_mock_provider_passes_generation_and_review() -> None:
    plan, review = ScriptService(MockLLMProvider()).generate_and_review(
        "Secure Boot", "learners"
    )
    assert len(plan.scenes) == 5
    assert review.approved is True