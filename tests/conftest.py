"""Shared fixtures: sample items, a fake Anthropic client, canned digests."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from digest.models import Digest, Item, QuickHit, RankedItem, RankingResponse, TopStory, Trend

NOW = datetime(2026, 8, 17, 8, 0, tzinfo=UTC)


def make_item(i: int = 0, days_ago: int = 1, **overrides) -> Item:
    defaults = {
        "feed_name": "Test Feed",
        "title": f"Article {i}",
        "link": f"https://example.com/article-{i}",
        "summary": f"Summary of article {i} about LLM testing.",
        "published": NOW - timedelta(days=days_ago),
    }
    defaults.update(overrides)
    return Item(**defaults)


@pytest.fixture
def sample_items() -> list[Item]:
    return [make_item(i) for i in range(5)]


@pytest.fixture
def sample_digest() -> Digest:
    return Digest(
        headline="Evals go mainstream",
        overview="A busy week: two major model releases and new eval tooling.",
        top_stories=[
            TopStory(
                title="Article 0",
                link="https://example.com/article-0",
                source="Test Feed",
                summary="A new eval framework for conversational agents was released.",
                why_it_matters="Directly applicable to regression-testing LLM workflows.",
            )
        ],
        quick_hits=[
            QuickHit(
                title="Article 1",
                link="https://example.com/article-1",
                source="Test Feed",
                one_liner="pytest 9 adds native async fixtures.",
            )
        ],
        trends=[Trend(name="LLM-as-judge", evidence="Mentioned in 3 separate posts this week.")],
        career_implications=["Try the new eval framework on a toy RAG pipeline."],
        quiet_week=False,
    )


class FakeParsedResponse:
    def __init__(self, parsed_output):
        self.parsed_output = parsed_output


class FakeMessages:
    """Stands in for client.messages; returns queued parse results in order."""

    def __init__(self, parse_results):
        self._results = list(parse_results)
        self.parse_calls: list[dict] = []

    def parse(self, **kwargs):
        self.parse_calls.append(kwargs)
        result = self._results.pop(0)
        if isinstance(result, Exception):
            raise result
        return FakeParsedResponse(result)


def fake_client(parse_results) -> SimpleNamespace:
    return SimpleNamespace(messages=FakeMessages(parse_results))


def full_ranking(n: int, score: int = 8, topic: str = "LLM evals") -> RankingResponse:
    return RankingResponse(
        rankings=[RankedItem(index=i, score=score, topic=topic) for i in range(n)]
    )
