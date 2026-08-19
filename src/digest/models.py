"""Data models shared across the pipeline."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Feed(BaseModel):
    name: str
    url: str
    category: str = "uncategorized"


class Item(BaseModel):
    """One article pulled from a feed."""

    feed_name: str
    title: str
    link: str
    summary: str = ""
    published: datetime | None = None


class RankedItem(BaseModel):
    """LLM relevance judgment for one item (index refers to the batch sent)."""

    index: int
    score: int = Field(ge=0, le=10)
    topic: str


class RankingResponse(BaseModel):
    rankings: list[RankedItem]


class TopStory(BaseModel):
    title: str
    link: str
    source: str
    summary: str
    why_it_matters: str


class QuickHit(BaseModel):
    title: str
    link: str
    source: str
    one_liner: str


class Trend(BaseModel):
    name: str
    evidence: str


class Digest(BaseModel):
    """The analyst's weekly output, rendered into the email."""

    headline: str
    overview: str
    top_stories: list[TopStory]
    quick_hits: list[QuickHit]
    trends: list[Trend]
    career_implications: list[str]
    quiet_week: bool = False


class FetchReport(BaseModel):
    items: list[Item]
    failed_feeds: list[str]
