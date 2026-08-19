"""Analysis pass: the stronger model writes the weekly digest from top-ranked items."""
from __future__ import annotations

import logging

import anthropic

from .config import (
    ANALYSIS_MODEL,
    ANALYZE_SUMMARY_CHARS,
    MAX_ANALYZED_ITEMS,
    QUIET_WEEK_THRESHOLD,
    RELEVANCE_THRESHOLD,
    TARGET_ROLE_PROFILE,
)
from .models import Digest, Item

log = logging.getLogger(__name__)

ANALYSIS_SYSTEM = f"""You are a sharp weekly news analyst writing a personal briefing in English.

{TARGET_ROLE_PROFILE}

From the articles provided, produce the weekly digest:
- headline: one punchy line naming the week's dominant theme
- overview: 2-3 sentences on the week as a whole
- top_stories: the 3-6 most important items. Each summary is 2-3 factual sentences;
  why_it_matters is 1-2 sentences tying the story to the reader's work in AI reliability
  and test automation (be concrete: what to try, watch, or mention in an interview)
- quick_hits: 4-10 remaining worthwhile items, one line each
- trends: 1-3 patterns visible across multiple items this week, with the evidence
- career_implications: 2-4 actionable takeaways (skills to practice, tools to look at,
  talking points for interviews in this field)
- quiet_week: set true only if told the week was quiet

Use only the articles given — never invent stories, links, or sources.
Every top story and quick hit must reuse the exact link provided for that article."""


def select_top(ranked: list[tuple[Item, int, str]]) -> list[tuple[Item, int, str]]:
    relevant = [r for r in ranked if r[1] >= RELEVANCE_THRESHOLD]
    relevant.sort(key=lambda r: r[1], reverse=True)
    return relevant[:MAX_ANALYZED_ITEMS]


def _articles_block(selected: list[tuple[Item, int, str]]) -> str:
    parts = []
    for item, score, topic in selected:
        date = item.published.strftime("%Y-%m-%d") if item.published else "undated"
        parts.append(
            f"### {item.title}\n"
            f"source: {item.feed_name} | date: {date} | link: {item.link}\n"
            f"relevance: {score}/10 | topic: {topic}\n"
            f"{item.summary[:ANALYZE_SUMMARY_CHARS]}"
        )
    return "\n\n".join(parts)


def analyze(client: anthropic.Anthropic, ranked: list[tuple[Item, int, str]]) -> Digest:
    selected = select_top(ranked)
    quiet = len(selected) < QUIET_WEEK_THRESHOLD

    if not selected:
        return Digest(
            headline="A quiet week in AI reliability",
            overview=(
                "No sufficiently relevant stories surfaced from the tracked feeds this week. "
                "The pipeline ran normally."
            ),
            top_stories=[],
            quick_hits=[],
            trends=[],
            career_implications=[],
            quiet_week=True,
        )

    prompt = (
        f"This week's top-ranked articles ({len(selected)}). "
        + ("NOTE: this was a quiet week with few relevant items.\n\n" if quiet else "\n\n")
        + _articles_block(selected)
    )

    response = client.messages.parse(
        model=ANALYSIS_MODEL,
        max_tokens=16000,
        system=ANALYSIS_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        output_format=Digest,
    )
    digest = response.parsed_output
    digest.quiet_week = quiet
    return digest
