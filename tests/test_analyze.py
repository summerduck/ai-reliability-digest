"""Analysis stage: selection, quiet-week logic, prompt content."""
from __future__ import annotations

from conftest import fake_client, make_item

from digest import analyze as analyze_mod
from digest.analyze import analyze, select_top
from digest.config import MAX_ANALYZED_ITEMS, RELEVANCE_THRESHOLD


def ranked(scores):
    return [(make_item(i), s, "topic") for i, s in enumerate(scores)]


def test_select_top_filters_below_threshold():
    selected = select_top(ranked([2, RELEVANCE_THRESHOLD, 10, 5]))
    assert [s for _, s, _ in selected] == [10, RELEVANCE_THRESHOLD]


def test_select_top_caps_item_count():
    selected = select_top(ranked([10] * (MAX_ANALYZED_ITEMS + 20)))
    assert len(selected) == MAX_ANALYZED_ITEMS


def test_no_relevant_items_returns_local_quiet_digest():
    client = fake_client([])  # must not be called
    digest = analyze(client, ranked([1, 0, 2]))
    assert digest.quiet_week is True
    assert digest.top_stories == []
    assert client.messages.parse_calls == []


def test_few_relevant_items_marks_quiet_week(sample_digest):
    client = fake_client([sample_digest])
    digest = analyze(client, ranked([9, 8]))
    assert digest.quiet_week is True
    assert "quiet week" in client.messages.parse_calls[0]["messages"][0]["content"].lower()


def test_busy_week_not_quiet(sample_digest):
    client = fake_client([sample_digest])
    digest = analyze(client, ranked([9] * 10))
    assert digest.quiet_week is False


def test_prompt_includes_links_and_sources(sample_digest):
    client = fake_client([sample_digest])
    analyze(client, ranked([9] * 6))
    prompt = client.messages.parse_calls[0]["messages"][0]["content"]
    assert "https://example.com/article-0" in prompt
    assert "Test Feed" in prompt


def test_analysis_uses_configured_model(sample_digest):
    client = fake_client([sample_digest])
    analyze(client, ranked([9] * 6))
    assert client.messages.parse_calls[0]["model"] == analyze_mod.ANALYSIS_MODEL
