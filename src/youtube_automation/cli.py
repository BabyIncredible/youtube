"""Command-line entry points for running and inspecting the pipeline."""

from __future__ import annotations

import argparse
import json
import re
import secrets
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from youtube_automation.config import load_config
from youtube_automation.providers.mock import MockLLMProvider
from youtube_automation.services.topic_service import TopicService
from youtube_automation.state import PipelineState
from youtube_automation.utils.files import atomic_write_json


def _run_id(topic: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", topic.casefold()).strip("-")[:48] or "video"
    return f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{slug}-{secrets.token_hex(2)}"


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser without reading configuration or credentials."""
    parser = argparse.ArgumentParser(prog="youtube-automation")
    parser.add_argument("--config", type=Path, default=Path("config.yaml"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="start a new pipeline run")
    run_parser.add_argument("--topic")
    run_parser.add_argument("--privacy", choices=("private", "unlisted", "public"), default="private")
    run_parser.add_argument("--mock-providers", action="store_true", required=True)
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--no-upload", action="store_true")

    subparsers.add_parser("list-topics", help="show configured topic statuses")
    return parser


def _run(args: argparse.Namespace) -> int:
    config, _environment = load_config(args.config)
    topics = TopicService(Path("topics.csv"))
    claimed_topic_id: str | None = None
    run_id = _run_id(args.topic or "queued-topic")
    if args.topic:
        topic_title, audience = args.topic, "general technical audience"
    elif args.dry_run:
        available = [row for row in topics.list_rows() if row["status"] == "pending"]
        if not available:
            raise LookupError("No pending topics are available")
        selected = max(available, key=lambda row: int(row["priority"]))
        topic_title, audience = selected["title"], selected["audience"]
    else:
        selected_topic = topics.select(run_id)
        claimed_topic_id = selected_topic.topic_id
        topic_title, audience = selected_topic.title, selected_topic.audience

    run_directory = config.pipeline.output_directory / run_id
    run_directory.mkdir(parents=True, exist_ok=False)
    state = PipelineState(run_id=run_id, topic_id=claimed_topic_id)
    state.start_stage("plan_generated")
    plan = MockLLMProvider().generate_video_plan(topic_title, audience, ())
    plan_path = run_directory / "video_plan.json"
    atomic_write_json(plan_path, plan.model_dump(mode="json"))
    state.complete_stage("plan_generated", [plan_path])
    state.save(run_directory / "state.json")
    print(json.dumps({"run_id": run_id, "output_directory": str(run_directory)}, indent=2))
    return 0


def _list_topics() -> int:
    for row in TopicService(Path("topics.csv")).list_rows():
        print(f"{row['status']:10} {row['priority']:>3}  {row['title']}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and return a process-compatible exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return _run(args)
        if args.command == "list-topics":
            return _list_topics()
    except (OSError, ValueError, LookupError, RuntimeError) as exc:
        parser.exit(1, f"error: {exc}\n")
    return 1
