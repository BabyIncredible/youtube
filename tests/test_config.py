"""Tests for startup configuration validation."""

from pathlib import Path

import pytest

from youtube_automation.config import load_config
from youtube_automation.exceptions import ConfigurationError


def test_example_configuration_loads() -> None:
    config, _environment = load_config(Path("config.example.yaml"))
    assert config.video.width == 1920
    assert config.channel.default_privacy == "private"


def test_missing_configuration_has_actionable_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="Copy config.example.yaml"):
        load_config(tmp_path / "missing.yaml")