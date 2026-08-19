"""End-to-end: fixture feeds through the whole pipeline to rendered HTML and dry run."""
from __future__ import annotations

import time
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

from conftest import NOW, fake_client, full_ranking

from digest.main import build_digest_html


def _entry(i):
    e = SimpleNamespace(
        title=f"Real story {i}",
        link=f"https://news.example.com/{i}",
        summary=f"<p>Details of story {i} about evals.</p>",
    )
    e.published_parsed = time.gmtime((NOW - timedelta(days=1)).timestamp())
    return e


def test_pipeline_produces_full_email(sample_digest, tmp_path):
    feeds_yaml = tmp_path / "feeds.yaml"
    feeds_yaml.write_text(
        "feeds:\n"
        "  - name: Feed A\n    url: https://a.example.com/rss\n    category: ai\n"
        "  - name: Feed B\n    url: https://b.example.com/rss\n    category: testing\n"
    )
    ok = SimpleNamespace(entries=[_entry(i) for i in range(8)], bozo=False)
    broken = SimpleNamespace(entries=[], bozo=True)
    client = fake_client([full_ranking(8, score=9), sample_digest])

    with (
        patch("digest.main.load_feeds", lambda: __import__("digest.config", fromlist=["load_feeds"]).load_feeds(feeds_yaml)),
        patch("digest.fetch.feedparser.parse", side_effect=[ok, broken]),
    ):
        subject, html = build_digest_html(client)

    assert sample_digest.headline in subject
    assert sample_digest.headline in html
    assert "Feed B" in html  # broken feed surfaces in the footer
    assert len(client.messages.parse_calls) == 2  # one ranking batch + one analysis
