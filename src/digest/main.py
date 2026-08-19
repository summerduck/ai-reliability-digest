"""Pipeline entry point: fetch → rank → analyze → render → send.

Usage:
    python -m digest.main              # full run, sends the email
    python -m digest.main --dry-run    # writes digest.html instead of sending
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import anthropic

from .analyze import analyze
from .config import Settings, load_feeds
from .fetch import fetch_all
from .rank import rank_items
from .render import render_html, subject_line
from .send import send_email

log = logging.getLogger(__name__)


def build_digest_html(client: anthropic.Anthropic) -> tuple[str, str]:
    """Run the pipeline; returns (subject, html)."""
    feeds = load_feeds()
    log.info("Fetching %d feeds", len(feeds))
    report = fetch_all(feeds)
    log.info("Fetched %d items; %d feeds failed", len(report.items), len(report.failed_feeds))

    ranked = rank_items(client, report.items)
    digest = analyze(client, ranked)

    today = datetime.now(UTC).date()
    return subject_line(digest, today), render_html(digest, report.failed_feeds, today)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and send the weekly digest")
    parser.add_argument("--dry-run", action="store_true", help="write digest.html, don't email")
    parser.add_argument("--out", default="digest.html", help="output path for --dry-run")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    settings = Settings()
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    subject, body = build_digest_html(client)

    if args.dry_run:
        Path(args.out).write_text(body)
        log.info("Dry run: wrote %s (subject: %s)", args.out, subject)
        return 0

    settings.require_email()
    send_email(
        sender=settings.gmail_address,
        app_password=settings.gmail_app_password,
        recipient=settings.digest_to,
        subject=subject,
        html_body=body,
    )
    log.info("Sent digest to %s", settings.digest_to)
    return 0


if __name__ == "__main__":
    sys.exit(main())
