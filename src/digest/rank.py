"""Relevance ranking pass: cheap model scores every item against the role profile."""
from __future__ import annotations

import logging

import anthropic
import pydantic

from .config import (
    RANK_BATCH_SIZE,
    RANK_SUMMARY_CHARS,
    RANKING_MODEL,
    TARGET_ROLE_PROFILE,
)
from .models import Item, RankingResponse

log = logging.getLogger(__name__)

RANKING_SYSTEM = f"""You are a news relevance scorer.

{TARGET_ROLE_PROFILE}

Score each numbered article 0-10 for how useful it is to this reader:
10 = must-read (directly about testing/evaluating LLM systems, or a major model release),
6-9 = clearly relevant, 3-5 = tangential, 0-2 = noise.
Also assign each article a short topic label (2-4 words, e.g. "LLM evals", "model release",
"RAG", "testing tooling", "observability").
Return one ranking per article, using the article's number as its index."""


def _batch_prompt(batch: list[Item], offset: int) -> str:
    lines = []
    for i, item in enumerate(batch):
        summary = item.summary[:RANK_SUMMARY_CHARS]
        lines.append(f"[{offset + i}] ({item.feed_name}) {item.title}\n{summary}")
    return "Score these articles:\n\n" + "\n\n".join(lines)


def rank_items(client: anthropic.Anthropic, items: list[Item]) -> list[tuple[Item, int, str]]:
    """Return (item, score, topic) for every item; a failed batch scores 0."""
    results: list[tuple[Item, int, str]] = []
    for start in range(0, len(items), RANK_BATCH_SIZE):
        batch = items[start : start + RANK_BATCH_SIZE]
        scores = {i: (0, "unranked") for i in range(start, start + len(batch))}
        try:
            response = client.messages.parse(
                model=RANKING_MODEL,
                max_tokens=8000,
                system=RANKING_SYSTEM,
                messages=[{"role": "user", "content": _batch_prompt(batch, start)}],
                output_format=RankingResponse,
            )
            for ranked in response.parsed_output.rankings:
                if ranked.index in scores:
                    scores[ranked.index] = (ranked.score, ranked.topic)
        # ValidationError: messages.parse raises it when the model's JSON
        # doesn't match the schema — must degrade, not kill the issue.
        except (anthropic.APIError, pydantic.ValidationError):
            log.exception("Ranking batch starting at %d failed; items score 0", start)
        for i, item in enumerate(batch):
            score, topic = scores[start + i]
            results.append((item, score, topic))
    return results
