"""Tests for atomic topic selection and status updates."""

from pathlib import Path

from youtube_automation.services.topic_service import TopicService


CSV = """topic_id,title,audience,status,priority,created_at,completed_at,run_id
low,Low priority,learners,pending,1,2026-08-30,,
high,High priority,learners,pending,10,2026-08-30,,
"""


def test_select_claims_highest_priority_topic(tmp_path: Path) -> None:
    path = tmp_path / "topics.csv"
    path.write_text(CSV, encoding="utf-8")
    service = TopicService(path)

    selected = service.select("run-123")

    assert selected.topic_id == "high"
    high = next(row for row in service.list_rows() if row["topic_id"] == "high")
    assert high["status"] == "processing"
    assert high["run_id"] == "run-123"


def test_status_update_preserves_topic_data(tmp_path: Path) -> None:
    path = tmp_path / "topics.csv"
    path.write_text(CSV, encoding="utf-8")
    service = TopicService(path)
    service.update_status("low", "failed")
    row = next(row for row in service.list_rows() if row["topic_id"] == "low")
    assert row["title"] == "Low priority"
    assert row["status"] == "failed"
