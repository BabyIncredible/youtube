# YouTube Automation

A modular Python pipeline for producing educational, faceless YouTube videos.
Phase 1 provides configuration, validated video-plan models, atomic topic and
pipeline-state persistence, deterministic mock planning, and the command-line
entry point. Media generation and uploading are built in later phases.

## Quick start

Requires Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp config.example.yaml config.yaml
python -m youtube_automation --help
python -m youtube_automation list-topics
python -m youtube_automation run --mock-providers --dry-run
```

Never put credentials in `config.yaml`; copy `.env.example` to `.env` and add
secrets locally. `.env` and YouTube OAuth files are ignored by Git.
