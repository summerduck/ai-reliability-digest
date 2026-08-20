"""Render stage: HTML structure, escaping, quiet week, failed-feed footer."""
from __future__ import annotations

from datetime import date

from digest.models import Digest, TopStory
from digest.render import render_html, subject_line

ISSUE_DATE = date(2026, 8, 17)


def test_all_sections_rendered(sample_digest):
    html = render_html(sample_digest, [], ISSUE_DATE)
    assert sample_digest.headline in html
    assert "Top stories" in html
    assert "Quick hits" in html
    assert "Trends this week" in html
    assert "For your career" in html
    assert "https://example.com/article-0" in html
    assert "6 min read" in html


def test_failed_feeds_listed_in_footer(sample_digest):
    html = render_html(sample_digest, ["Dead Feed", "Slow Feed"], ISSUE_DATE)
    assert "Dead Feed, Slow Feed" in html


def test_no_failed_feeds_no_warning(sample_digest):
    assert "unreachable" not in render_html(sample_digest, [], ISSUE_DATE)


def test_quiet_week_badge(sample_digest):
    sample_digest.quiet_week = True
    assert "quiet week" in render_html(sample_digest, [], ISSUE_DATE)


def test_html_in_content_is_escaped(sample_digest):
    sample_digest.top_stories.append(
        TopStory(
            title="<script>alert(1)</script>",
            link="https://example.com/x",
            source="Feed <b>",
            summary="a & b",
            why_it_matters="safe",
            reading_minutes=3,
        )
    )
    html = render_html(sample_digest, [], ISSUE_DATE)
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_empty_sections_omitted():
    digest = Digest(
        headline="Quiet",
        overview="Nothing happened.",
        top_stories=[],
        quick_hits=[],
        trends=[],
        career_implications=[],
        quiet_week=True,
    )
    html = render_html(digest, [], ISSUE_DATE)
    assert "Top stories" not in html
    assert "Quick hits" not in html


def test_subject_line(sample_digest):
    subject = subject_line(sample_digest, ISSUE_DATE)
    assert "Aug 17" in subject
    assert sample_digest.headline in subject
    assert "quiet" not in subject
    sample_digest.quiet_week = True
    assert "quiet week" in subject_line(sample_digest, ISSUE_DATE)
