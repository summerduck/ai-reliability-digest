"""Configuration: feeds file, models, env-var settings."""
from __future__ import annotations

import os
from pathlib import Path

import yaml

from .models import Feed

RANKING_MODEL = "claude-haiku-4-5"
ANALYSIS_MODEL = "claude-sonnet-5"

# How far back one issue looks (GitHub Actions is stateless, so a fixed window
# instead of persisted seen-item state).
WINDOW_DAYS = 7

# Items scoring >= this go to the analysis pass.
RELEVANCE_THRESHOLD = 6
# Cap on items sent to the analysis pass.
MAX_ANALYZED_ITEMS = 25
# Fewer than this many relevant items marks the issue a "quiet week".
QUIET_WEEK_THRESHOLD = 5
# Items per ranking batch (keeps each Haiku request small and parseable).
RANK_BATCH_SIZE = 50
# Truncation for summaries fed to the LLM passes.
RANK_SUMMARY_CHARS = 300
ANALYZE_SUMMARY_CHARS = 1500

FEEDS_FILE = Path(__file__).resolve().parents[2] / "feeds.yaml"

TARGET_ROLE_PROFILE = """\
The reader is an engineer targeting an "AI Reliability & Test Automation Engineer" role
on an LLM team building real-time conversational AI (LLMs, ASR, TTS). Relevant topics:
- Testing and evaluating LLM-powered systems: evals, regression testing for prompts/models,
  testing non-deterministic and distributed systems, LLM-as-judge, benchmarks
- Test automation craft: pytest, mocks/fixtures, test harnesses, API testing, CI/CD test gates
- Major model releases and capability changes (Anthropic, OpenAI, Google DeepMind, Meta,
  open-source models) — especially anything affecting reliability, regressions, or evals
- RAG pipelines, conversational AI, agents, ASR/TTS
- Load/stress testing, observability, production telemetry, failure analysis, SRE practice
- Python engineering and tooling
Less relevant: consumer gadget news, funding rounds without technical substance, design,
crypto, general business news.\
"""


def load_feeds(path: Path | None = None) -> list[Feed]:
    raw = yaml.safe_load((path or FEEDS_FILE).read_text())
    return [Feed(**entry) for entry in raw["feeds"]]


class Settings:
    """Runtime settings from environment variables (set in GitHub Secrets)."""

    def __init__(self) -> None:
        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.gmail_address = os.environ.get("GMAIL_ADDRESS", "")
        self.gmail_app_password = os.environ.get("GMAIL_APP_PASSWORD", "")
        self.digest_to = os.environ.get("DIGEST_TO", self.gmail_address)

    def require_email(self) -> None:
        missing = [
            name
            for name, value in [
                ("GMAIL_ADDRESS", self.gmail_address),
                ("GMAIL_APP_PASSWORD", self.gmail_app_password),
            ]
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
