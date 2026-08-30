"""Validated domain models exchanged between providers and pipeline services."""

from __future__ import annotations

from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator


_url_adapter = TypeAdapter(AnyHttpUrl)


def _validate_urls(urls: list[str]) -> list[str]:
    """Validate URLs without adding unsupported URI formats to provider schemas."""
    for url in urls:
        _url_adapter.validate_python(url)
    return urls


class Scene(BaseModel):
    """Narration and visual direction for one sequential video scene."""

    model_config = ConfigDict(extra="forbid")
    scene_id: int = Field(ge=1)
    narration: str = Field(min_length=1)
    visual_type: Literal["generated_image", "diagram", "stock_video"]
    visual_prompt: str = Field(min_length=1)
    on_screen_text: str = Field(max_length=80)
    transition: str = Field(min_length=1)
    source_urls: list[str]

    _validate_source_urls = field_validator("source_urls")(_validate_urls)


class ThumbnailPlan(BaseModel):
    """Text and background prompt used to create the thumbnail."""

    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1)
    image_prompt: str = Field(min_length=1)

    @field_validator("text")
    @classmethod
    def limit_text_words(cls, value: str) -> str:
        """Keep thumbnail copy within the configured YouTube design limit."""
        if len(value.split()) > 6:
            raise ValueError("thumbnail text must contain at most six words")
        return value


class VideoPlan(BaseModel):
    """Complete structured plan returned by an LLM provider."""

    model_config = ConfigDict(extra="forbid")
    topic: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=5000)
    audience: str = Field(min_length=1)
    hook: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    tags: list[str] = Field(min_length=1)
    source_urls: list[str]
    scenes: list[Scene] = Field(min_length=5, max_length=20)
    thumbnail: ThumbnailPlan
    contains_realistic_synthetic_media: bool

    _validate_source_urls = field_validator("source_urls")(_validate_urls)

    @field_validator("tags")
    @classmethod
    def normalize_unique_tags(cls, tags: list[str]) -> list[str]:
        """Trim tags and reject duplicates regardless of letter case."""
        normalized = [tag.strip() for tag in tags if tag.strip()]
        folded = [tag.casefold() for tag in normalized]
        if len(folded) != len(set(folded)):
            raise ValueError("tags must be unique after case-insensitive normalization")
        if not normalized:
            raise ValueError("at least one non-empty tag is required")
        return normalized

    @model_validator(mode="after")
    def validate_scene_sequence(self) -> "VideoPlan":
        """Require scene identifiers to be exactly 1 through the scene count."""
        expected = list(range(1, len(self.scenes) + 1))
        actual = [scene.scene_id for scene in self.scenes]
        if actual != expected:
            raise ValueError(f"scene IDs must be sequential; expected {expected}")
        return self


class ReviewResult(BaseModel):
    """Structured editorial decision returned by the LLM review pass."""

    model_config = ConfigDict(extra="forbid")
    approved: bool
    issues: list[str]
    summary: str = Field(min_length=1)
