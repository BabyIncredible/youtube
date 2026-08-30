"""Tests for the OpenAI structured-output adapter without network calls."""

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from youtube_automation.models import VideoPlan
from youtube_automation.providers.mock import MockLLMProvider
from youtube_automation.providers.openai import OpenAIProvider


class FakeResponses:
    """Capture structured parse arguments and return a prepared value."""

    def __init__(self, parsed: Any) -> None:
        self.parsed = parsed
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


def test_generate_uses_configured_model_and_video_plan_schema(tmp_path: Path) -> None:
    prompt_directory = tmp_path / "prompts"
    prompt_directory.mkdir()
    (prompt_directory / "script_generation.txt").write_text("Return JSON.", encoding="utf-8")
    plan = MockLLMProvider().generate_video_plan("Secure Boot", "learners", ())
    responses = FakeResponses(plan)
    client = SimpleNamespace(responses=responses)
    provider = OpenAIProvider(
        api_key="test-key",
        model="configured-model",
        prompt_directory=prompt_directory,
        client=client,
    )

    result = provider.generate_video_plan("Secure Boot", "learners", ())

    assert result == plan
    assert responses.calls[0]["model"] == "configured-model"
    assert responses.calls[0]["text_format"] is VideoPlan
    assert "Secure Boot" in responses.calls[0]["input"]


def test_correction_details_are_sent_to_provider(tmp_path: Path) -> None:
    prompt_directory = tmp_path / "prompts"
    prompt_directory.mkdir()
    (prompt_directory / "script_generation.txt").write_text("Return JSON.", encoding="utf-8")
    plan = MockLLMProvider().generate_video_plan("Secure Boot", "learners", ())
    responses = FakeResponses(plan)
    provider = OpenAIProvider(
        api_key="test-key",
        model="configured-model",
        prompt_directory=prompt_directory,
        client=SimpleNamespace(responses=responses),
    )

    provider.generate_video_plan("Secure Boot", "learners", (), "fix scene IDs")

    assert "fix scene IDs" in responses.calls[0]["input"]
