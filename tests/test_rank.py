"""Ranking stage: batching, score mapping, failed-batch degradation."""
from __future__ import annotations

import anthropic
import httpx
from conftest import fake_client, full_ranking, make_item

from digest import rank
from digest.models import RankedItem, RankingResponse


def test_scores_mapped_back_to_items(sample_items):
    client = fake_client([full_ranking(len(sample_items), score=7)])
    results = rank.rank_items(client, sample_items)
    assert len(results) == len(sample_items)
    assert all(score == 7 for _, score, _ in results)
    assert [item.title for item, _, _ in results] == [i.title for i in sample_items]


def test_items_split_into_batches(monkeypatch, sample_items):
    monkeypatch.setattr(rank, "RANK_BATCH_SIZE", 2)
    client = fake_client([full_ranking(2), full_ranking(2), full_ranking(1)])
    # Batch indices are global, so shift each canned response's indices.
    client.messages._results[1] = RankingResponse(
        rankings=[RankedItem(index=2, score=8, topic="t"), RankedItem(index=3, score=8, topic="t")]
    )
    client.messages._results[2] = RankingResponse(
        rankings=[RankedItem(index=4, score=8, topic="t")]
    )
    results = rank.rank_items(client, sample_items)
    assert len(client.messages.parse_calls) == 3
    assert all(score == 8 for _, score, _ in results)


def test_failed_batch_scores_zero_and_run_continues(monkeypatch, sample_items):
    monkeypatch.setattr(rank, "RANK_BATCH_SIZE", 3)
    api_error = anthropic.APIStatusError(
        "boom",
        response=httpx.Response(500, request=httpx.Request("POST", "https://api.test")),
        body=None,
    )
    second = RankingResponse(
        rankings=[RankedItem(index=3, score=9, topic="t"), RankedItem(index=4, score=9, topic="t")]
    )
    client = fake_client([api_error, second])
    results = rank.rank_items(client, sample_items)
    assert [score for _, score, _ in results] == [0, 0, 0, 9, 9]


def test_out_of_range_index_ignored():
    items = [make_item(0)]
    response = RankingResponse(
        rankings=[RankedItem(index=0, score=5, topic="t"), RankedItem(index=99, score=10, topic="t")]
    )
    client = fake_client([response])
    results = rank.rank_items(client, items)
    assert results[0][1] == 5


def test_empty_item_list_makes_no_api_calls():
    client = fake_client([])
    assert rank.rank_items(client, []) == []
    assert client.messages.parse_calls == []


def test_prompt_contains_titles_and_truncated_summaries(sample_items):
    long_item = make_item(0, summary="x" * 5000)
    client = fake_client([full_ranking(1)])
    rank.rank_items(client, [long_item])
    prompt = client.messages.parse_calls[0]["messages"][0]["content"]
    assert "Article 0" in prompt
    assert "x" * (rank.RANK_SUMMARY_CHARS + 1) not in prompt
