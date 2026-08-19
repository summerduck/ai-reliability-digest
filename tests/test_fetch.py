"""Fetch stage: window filtering, failure collection, dedup, HTML stripping."""
from __future__ import annotations

import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from conftest import NOW

from digest.fetch import fetch_all
from digest.models import Feed

FEED = Feed(name="Test Feed", url="https://example.com/rss")


def entry(title="Story", link="https://example.com/a", summary="text", published=None):
    e = SimpleNamespace(title=title, link=link, summary=summary)
    if published is not None:
        e.published_parsed = time.gmtime(published.timestamp())
    return e


def parsed(entries, bozo=False):
    return SimpleNamespace(entries=entries, bozo=bozo)


def test_recent_items_kept_old_items_dropped():
    entries = [
        entry(title="Fresh", link="https://e.com/1", published=NOW - timedelta(days=2)),
        entry(title="Stale", link="https://e.com/2", published=NOW - timedelta(days=30)),
    ]
    with patch("digest.fetch.feedparser.parse", return_value=parsed(entries)):
        report = fetch_all([FEED], now=NOW)
    assert [i.title for i in report.items] == ["Fresh"]
    assert report.failed_feeds == []


def test_undated_items_are_kept():
    with patch("digest.fetch.feedparser.parse", return_value=parsed([entry(title="No date")])):
        report = fetch_all([FEED], now=NOW)
    assert len(report.items) == 1
    assert report.items[0].published is None


def test_broken_feed_reported_not_fatal():
    ok = parsed([entry(published=NOW - timedelta(days=1))])
    broken = parsed([], bozo=True)
    feeds = [FEED, Feed(name="Broken Feed", url="https://broken.example.com/rss")]
    with patch("digest.fetch.feedparser.parse", side_effect=[ok, broken]):
        report = fetch_all(feeds, now=NOW)
    assert report.failed_feeds == ["Broken Feed"]
    assert len(report.items) == 1


def test_parser_exception_reported_not_fatal():
    with patch("digest.fetch.feedparser.parse", side_effect=OSError("dns")):
        report = fetch_all([FEED], now=NOW)
    assert report.failed_feeds == ["Test Feed"]


def test_duplicate_links_deduped():
    entries = [
        entry(title="Same story", link="https://e.com/dup", published=NOW - timedelta(days=1)),
        entry(title="Same story again", link="https://e.com/dup", published=NOW - timedelta(days=1)),
    ]
    with patch("digest.fetch.feedparser.parse", return_value=parsed(entries)):
        report = fetch_all([FEED], now=NOW)
    assert len(report.items) == 1


def test_html_stripped_from_title_and_summary():
    e = entry(
        title="<b>Bold</b> title &amp; more",
        summary="<p>Hello <a href='x'>world</a></p>",
        published=NOW - timedelta(days=1),
    )
    with patch("digest.fetch.feedparser.parse", return_value=parsed([e])):
        report = fetch_all([FEED], now=NOW)
    assert report.items[0].title == "Bold title & more"
    assert "<" not in report.items[0].summary
    assert "Hello" in report.items[0].summary


def test_empty_wellformed_feed_is_not_a_failure():
    with patch("digest.fetch.feedparser.parse", return_value=parsed([])):
        report = fetch_all([FEED], now=NOW)
    assert report.failed_feeds == []
    assert report.items == []
