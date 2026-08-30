"""Persistent, resumable pipeline stage state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from youtube_automation.exceptions import PipelineStateError
from youtube_automation.utils.files import atomic_write_json


class StageState(BaseModel):
    """Execution details for one idempotent pipeline stage."""

    model_config = ConfigDict(extra="forbid")
    status: str = "pending"
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output_paths: list[Path] = Field(default_factory=list)
    error_summary: str | None = None
    attempt_count: int = 0


class PipelineState(BaseModel):
    """Durable state for one run, written atomically after every transition."""

    model_config = ConfigDict(extra="forbid")
    run_id: str
    topic_id: str | None = None
    stages: dict[str, StageState] = Field(default_factory=dict)
    youtube_video_id: str | None = None

    def start_stage(self, name: str) -> None:
        """Record a stage attempt before side effects begin."""
        stage = self.stages.setdefault(name, StageState())
        stage.status = "running"
        stage.started_at = datetime.now(UTC)
        stage.completed_at = None
        stage.error_summary = None
        stage.attempt_count += 1

    def complete_stage(self, name: str, output_paths: list[Path]) -> None:
        """Record successful outputs for a stage."""
        stage = self.stages[name]
        stage.status = "completed"
        stage.completed_at = datetime.now(UTC)
        stage.output_paths = output_paths

    def save(self, path: Path) -> None:
        """Persist state atomically so interruption cannot corrupt it."""
        atomic_write_json(path, self.model_dump(mode="json"))

    @classmethod
    def load(cls, path: Path) -> "PipelineState":
        """Load and validate an existing state file."""
        try:
            return cls.model_validate(json.loads(path.read_text(encoding="utf-8")))
        except (OSError, ValueError) as exc:
            raise PipelineStateError(f"Cannot load pipeline state from {path}: {exc}") from exc
