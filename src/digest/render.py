"""Render a Digest into an HTML email body."""
from __future__ import annotations

import html
from datetime import date

from .models import Digest

_STYLE_BODY = (
    "margin:0 auto;max-width:640px;padding:24px 16px;"
    "font-family:-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
    "color:#1a1a2e;line-height:1.55;"
)
_STYLE_H2 = "font-size:15px;letter-spacing:0.08em;text-transform:uppercase;color:#5b5b7a;margin:32px 0 12px;"
_STYLE_CARD = "margin:0 0 20px;padding:14px 16px;background:#f6f6fb;border-radius:8px;"
_STYLE_LINK = "color:#3b4bd8;text-decoration:none;"
_STYLE_MUTED = "color:#8a8aa3;font-size:13px;"


def _e(text: str) -> str:
    return html.escape(text, quote=True)


def render_html(digest: Digest, failed_feeds: list[str], issue_date: date) -> str:
    parts: list[str] = []
    parts.append(f'<div style="{_STYLE_BODY}">')

    quiet_badge = (
        '<span style="background:#fff3cd;color:#8a6d1a;border-radius:4px;'
        'padding:2px 8px;font-size:12px;margin-left:8px;">quiet week</span>'
        if digest.quiet_week
        else ""
    )
    parts.append(
        f'<p style="{_STYLE_MUTED}">AI Reliability Weekly · {issue_date.strftime("%B %d, %Y")}'
        f"{quiet_badge}</p>"
    )
    parts.append(f'<h1 style="font-size:24px;margin:8px 0 12px;">{_e(digest.headline)}</h1>')
    parts.append(f'<p style="font-size:16px;">{_e(digest.overview)}</p>')

    if digest.top_stories:
        parts.append(f'<h2 style="{_STYLE_H2}">Top stories</h2>')
        for story in digest.top_stories:
            parts.append(
                f'<div style="{_STYLE_CARD}">'
                f'<a href="{_e(story.link)}" style="{_STYLE_LINK}font-weight:600;font-size:16px;">'
                f"{_e(story.title)}</a>"
                f'<span style="{_STYLE_MUTED}"> · {_e(story.source)} · '
                f"{story.reading_minutes} min read</span>"
                f'<p style="margin:8px 0 6px;">{_e(story.summary)}</p>'
                f'<p style="margin:0;color:#3d5a3d;"><strong>Why it matters:</strong> '
                f"{_e(story.why_it_matters)}</p></div>"
            )

    if digest.quick_hits:
        parts.append(f'<h2 style="{_STYLE_H2}">Quick hits</h2>')
        parts.append('<ul style="padding-left:20px;margin:0;">')
        for hit in digest.quick_hits:
            parts.append(
                f'<li style="margin:0 0 10px;"><a href="{_e(hit.link)}" style="{_STYLE_LINK}">'
                f"{_e(hit.title)}</a>"
                f'<span style="{_STYLE_MUTED}"> · {_e(hit.source)}</span><br>'
                f"{_e(hit.one_liner)}</li>"
            )
        parts.append("</ul>")

    if digest.trends:
        parts.append(f'<h2 style="{_STYLE_H2}">Trends this week</h2>')
        for trend in digest.trends:
            parts.append(
                f'<p style="margin:0 0 10px;"><strong>{_e(trend.name)}</strong> — '
                f"{_e(trend.evidence)}</p>"
            )

    if digest.career_implications:
        parts.append(f'<h2 style="{_STYLE_H2}">For your career</h2>')
        parts.append('<ol style="padding-left:20px;margin:0;">')
        for takeaway in digest.career_implications:
            parts.append(f'<li style="margin:0 0 8px;">{_e(takeaway)}</li>')
        parts.append("</ol>")

    if failed_feeds:
        parts.append(
            f'<p style="{_STYLE_MUTED}margin-top:32px;">⚠ Feeds unreachable this week: '
            f"{_e(', '.join(failed_feeds))}</p>"
        )
    parts.append(
        f'<p style="{_STYLE_MUTED}margin-top:24px;">Generated automatically · '
        "curated for the AI Reliability &amp; Test Automation role</p>"
    )
    parts.append("</div>")
    return "\n".join(parts)


def subject_line(digest: Digest, issue_date: date) -> str:
    prefix = "AI Reliability Weekly"
    quiet = " (quiet week)" if digest.quiet_week else ""
    return f"{prefix} · {issue_date.strftime('%b %d')}{quiet} — {digest.headline}"
