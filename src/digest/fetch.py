"""Fetch RSS/Atom feeds and normalize entries into Items."""
from __future__ import annotations

import calendar
import html
import logging
import re
from datetime import UTC, datetime, timedelta

import feedparser

from .config import WINDOW_DAYS
from .models import Feed, FetchReport, Item

log = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return " ".join(html.unescape(_TAG_RE.sub(" ", text)).split())


def _entry_published(entry) -> datetime | None:
    for attr in ("published_parsed", "updated_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            return datetime.fromtimestamp(calendar.timegm(parsed), tz=UTC)
    return None


def _entry_summary(entry) -> str:
    if getattr(entry, "summary", None):
        return _strip_html(entry.summary)
    content = getattr(entry, "content", None)
    if content:
        return _strip_html(content[0].get("value", ""))
    return ""


def fetch_all(feeds: list[Feed], now: datetime | None = None) -> FetchReport:
    """Fetch every feed; failures are collected, never fatal."""
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=WINDOW_DAYS)
    items: list[Item] = []
    failed: list[str] = []

    for feed in feeds:
        try:
            parsed = feedparser.parse(feed.url)
        except Exception:  # noqa: BLE001 — one bad feed must never kill the issue
            log.warning("Feed crashed the parser: %s", feed.name)
            failed.append(feed.name)
            continue
        if getattr(parsed, "bozo", False) and not parsed.entries:
            failed.append(feed.name)
            continue
        if not parsed.entries:
            # An empty but well-formed feed is quiet, not broken.
            continue
        for entry in parsed.entries:
            published = _entry_published(entry)
            # Items with no date are kept: dropping them silently loses stories.
            if published is not None and published < cutoff:
                continue
            title = _strip_html(getattr(entry, "title", "")).strip()
            link = getattr(entry, "link", "")
            if not title or not link:
                continue
            items.append(
                Item(
                    feed_name=feed.name,
                    title=title,
                    link=link,
                    summary=_entry_summary(entry),
                    published=published,
                )
            )

    # Same story syndicated by several feeds: keep the first occurrence.
    seen: set[str] = set()
    deduped = []
    for item in items:
        key = item.link or item.title
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return FetchReport(items=deduped, failed_feeds=failed)
