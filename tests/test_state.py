"""Tests for durable pipeline-state persistence."""

from pathlib import Path

from youtube_automation.state import PipelineState


def test_state_round_trip(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    state = PipelineState(run_id="run-123", topic_id="secure-boot")
    state.start_stage("plan_generated")
    state.complete_stage("plan_generated", [tmp_path / "video_plan.json"])
    state.save(state_path)

    loaded = PipelineState.load(state_path)

    assert loaded.stages["plan_generated"].status == "completed"
    assert loaded.stages["plan_generated"].attempt_count == 1