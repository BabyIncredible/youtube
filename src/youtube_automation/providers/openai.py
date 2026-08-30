"""OpenAI Responses API adapter for typed plan generation and review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Sequence, TypeVar

import openai
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from youtube_automation.exceptions import (
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderResponseError,
)
from youtube_automation.models import ReviewResult, VideoPlan

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class OpenAIProvider:
    """Generate typed content through OpenAI with bounded application retries."""

    def __init__(
        self,
        api_key: str,
        model: str,
        prompt_directory: Path = Path("prompts"),
        retry_attempts: int = 3,
        timeout_seconds: float = 60.0,
        client: Any | None = None,
    ) -> None:
        if not api_key:
            raise ProviderAuthenticationError("LLM_API_KEY is required for the OpenAI provider")
        if not model:
            raise ProviderAuthenticationError("LLM_MODEL is required for the OpenAI provider")
        self.model = model
        self.prompt_directory = prompt_directory
        self.retry_attempts = retry_attempts
        self.client = client or OpenAI(
            api_key=api_key,
            timeout=timeout_seconds,
            max_retries=0,
        )

    def generate_video_plan(
        self,
        topic: str,
        audience: str,
        sources: Sequence[str],
        correction: str | None = None,
    ) -> VideoPlan:
        """Generate a plan constrained directly by the Pydantic schema."""
        prompt = self._read_prompt("script_generation.txt")
        request = {
            "topic": topic,
            "audience": audience,
            "source_urls": list(sources),
        }
        if correction:
            request["correction_required"] = correction
        return self._parse(prompt, json.dumps(request, ensure_ascii=False), VideoPlan)

    def review_video_plan(self, plan: VideoPlan) -> ReviewResult:
        """Run an independent structured editorial review of a generated plan."""
        prompt = self._read_prompt("script_review.txt")
        return self._parse(prompt, plan.model_dump_json(), ReviewResult)

    def _read_prompt(self, name: str) -> str:
        try:
            return (self.prompt_directory / name).read_text(encoding="utf-8")
        except OSError as exc:
            raise ProviderResponseError(f"Cannot read prompt template {name}: {exc}") from exc

    def _parse(
        self,
        instructions: str,
        user_input: str,
        response_model: type[StructuredModel],
    ) -> StructuredModel:
        retrying = Retrying(
            stop=stop_after_attempt(self.retry_attempts),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type((ProviderRateLimitError, openai.APIConnectionError)),
            reraise=True,
        )
        for attempt in retrying:
            with attempt:
                try:
                    response = self.client.responses.parse(
                        model=self.model,
                        instructions=instructions,
                        input=user_input,
                        text_format=response_model,
                    )
                except openai.AuthenticationError as exc:
                    raise ProviderAuthenticationError("The LLM provider rejected its credentials") from exc
                except openai.RateLimitError as exc:
                    raise ProviderRateLimitError("The LLM provider rate limit was reached") from exc
                except openai.APIConnectionError:
                    raise
                except (openai.APIStatusError, ValidationError, ValueError) as exc:
                    raise ProviderResponseError(f"The LLM provider returned an invalid response: {exc}") from exc

                parsed = response.output_parsed
                if not isinstance(parsed, response_model):
                    raise ProviderResponseError("The LLM provider returned no valid structured output")
                return parsed
        raise ProviderResponseError("The LLM provider did not return a response")
