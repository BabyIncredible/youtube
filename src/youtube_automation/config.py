"""Load and validate non-secret YAML settings and environment credentials."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from youtube_automation.exceptions import ConfigurationError


class ChannelConfig(BaseModel):
    """YouTube channel defaults that affect generated metadata and uploads."""

    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1)
    default_language: str = Field(default="en", min_length=2)
    category_id: str = "28"
    default_privacy: Literal["private", "unlisted"] = "private"
    made_for_kids: bool


class VideoConfig(BaseModel):
    """Output dimensions and accepted duration boundaries."""

    model_config = ConfigDict(extra="forbid")
    width: int = Field(default=1920, ge=640)
    height: int = Field(default=1080, ge=360)
    fps: int = Field(default=30, ge=15, le=120)
    minimum_duration_seconds: float = Field(default=60, gt=0)
    maximum_duration_seconds: float = Field(default=900, gt=0)

    @model_validator(mode="after")
    def validate_duration_range(self) -> "VideoConfig":
        """Require the maximum duration to exceed the minimum duration."""
        if self.maximum_duration_seconds <= self.minimum_duration_seconds:
            raise ValueError("maximum duration must exceed minimum duration")
        return self


class ScenesConfig(BaseModel):
    """Limits applied to generated scene plans."""

    model_config = ConfigDict(extra="forbid")
    minimum_count: int = Field(default=5, ge=1)
    maximum_count: int = Field(default=20, ge=1)
    maximum_on_screen_text_length: int = Field(default=80, ge=1, le=200)

    @model_validator(mode="after")
    def validate_count_range(self) -> "ScenesConfig":
        """Require a non-empty ordered scene-count range."""
        if self.maximum_count < self.minimum_count:
            raise ValueError("maximum scene count cannot be below minimum scene count")
        return self


class PipelineConfig(BaseModel):
    """Persistence, retry, and upload defaults for pipeline runs."""

    model_config = ConfigDict(extra="forbid")
    output_directory: Path = Path("output")
    retry_attempts: int = Field(default=3, ge=1, le=10)
    keep_intermediate_files: bool = True
    upload_after_render: bool = False
    upload_privacy: Literal["private", "unlisted"] = "private"


class AppConfig(BaseModel):
    """Validated application configuration assembled from YAML."""

    model_config = ConfigDict(extra="forbid")
    channel: ChannelConfig
    video: VideoConfig = VideoConfig()
    scenes: ScenesConfig = ScenesConfig()
    pipeline: PipelineConfig = PipelineConfig()


class ProviderEnvironment(BaseModel):
    """Provider credentials and configurable model identifiers from the environment."""

    llm_api_key: str | None = None
    llm_model: str | None = None
    tts_api_key: str | None = None
    tts_model: str | None = None
    tts_voice_id: str | None = None
    image_api_key: str | None = None
    image_model: str | None = None
    youtube_client_secrets_file: Path | None = None
    youtube_token_file: Path | None = None

    @classmethod
    def from_environment(cls) -> "ProviderEnvironment":
        """Read known provider variables without logging their values."""
        values = {
            field_name: os.getenv(field_name.upper())
            for field_name in cls.model_fields
        }
        return cls.model_validate(values)


def load_config(path: Path = Path("config.yaml")) -> tuple[AppConfig, ProviderEnvironment]:
    """Load YAML settings and environment credentials, raising readable errors."""
    load_dotenv()
    if not path.is_file():
        raise ConfigurationError(
            f"Configuration file not found: {path}. Copy config.example.yaml to config.yaml."
        )
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ConfigurationError("Configuration root must be a YAML mapping")
        return AppConfig.model_validate(raw), ProviderEnvironment.from_environment()
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigurationError(f"Invalid configuration: {exc}") from exc
