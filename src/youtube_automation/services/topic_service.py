"""Atomic CSV-backed topic selection and lifecycle updates."""

from __future__ import annotations

import csv
import io
import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Literal

from youtube_automation.utils.files import atomic_write_text

TopicStatus = Literal["pending", "processing", "completed", "failed"]


@dataclass(frozen=True)
class Topic:
    """One topic row selected for a pipeline run."""

    topic_id: str
    title: str
    audience: str
    priority: int


class TopicService:
    """Coordinate topic selection using a short-lived exclusive lock file."""

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = csv_path
        self.lock_path = csv_path.with_suffix(csv_path.suffix + ".lock")

    @contextmanager
    def _lock(self) -> Iterator[None]:
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"Topic file is currently locked: {self.csv_path}") from exc
        os.close(descriptor)
        try:
            yield
        finally:
            self.lock_path.unlink(missing_ok=True)

    def list_rows(self) -> list[dict[str, str]]:
        """Return all topic rows without changing their status."""
        with self.csv_path.open(encoding="utf-8", newline="") as stream:
            return list(csv.DictReader(stream))

    def select(self, run_id: str) -> Topic:
        """Claim the highest-priority pending topic for a run atomically."""
        with self._lock():
            rows = self.list_rows()
            pending = [row for row in rows if row["status"] == "pending"]
            if not pending:
                raise LookupError("No pending topics are available")
            selected = max(pending, key=lambda row: int(row["priority"]))
            selected["status"] = "processing"
            selected["run_id"] = run_id
            self._write_rows(rows)
        return Topic(
            topic_id=selected["topic_id"],
            title=selected["title"],
            audience=selected["audience"],
            priority=int(selected["priority"]),
        )

    def update_status(self, topic_id: str, status: TopicStatus) -> None:
        """Update a claimed topic status while preserving all CSV columns."""
        with self._lock():
            rows = self.list_rows()
            for row in rows:
                if row["topic_id"] == topic_id:
                    row["status"] = status
                    break
            else:
                raise LookupError(f"Unknown topic ID: {topic_id}")
            self._write_rows(rows)

    def _write_rows(self, rows: list[dict[str, str]]) -> None:
        output = io.StringIO(newline="")
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        atomic_write_text(self.csv_path, output.getvalue())
