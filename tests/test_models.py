"""Tests for strict video-plan validation."""

import pytest
from pydantic import ValidationError

from youtube_automation.providers.mock import MockLLMProvider


def test_mock_plan_is_valid_and_sequential() -> None:
    plan = MockLLMProvider().generate_video_plan("Secure Boot", "learners", ())
    assert [scene.scene_id for scene in plan.scenes] == [1, 2, 3, 4, 5]


def test_duplicate_tags_are_rejected() -> None:
    plan = MockLLMProvider().generate_video_plan("Secure Boot", "learners", ())
    with pytest.raises(ValidationError, match="tags must be unique"):
        plan.model_copy(update={"tags": ["Firmware", "firmware"]}).model_validate(
            {**plan.model_dump(), "tags": ["Firmware", "firmware"]}
        )
