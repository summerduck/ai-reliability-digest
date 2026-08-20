"""Render a Digest into an HTML email body.

Design language: editorial warm monochrome with a single locked accent.
- Ink #111113 on warm off-white #FBFBFA; secondary #6E6E76; never pure black/white.
- One accent (emerald #1A7A54) carries links, the why-it-matters label, and state.
- No cards or shadows: sections and stories separate on 1px #E9E8E4 hairlines.
- Meta text (masthead, section labels, story numbers, reading time) is small
  tracked-caps monospace; headlines are large tight-tracked sans.
Email-safe: inline styles only, system font stacks, no images or scripts.
"""
from __future__ import annotations

import html
from datetime import date

from .models import Digest

_SANS = "-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
_MONO = "'SF Mono',SFMono-Regular,'Roboto Mono',Consolas,monospace"

_INK = "#111113"
_BODY_TEXT = "#37373D"
_MUTED = "#6E6E76"
_FAINT = "#9A9AA1"
_PAPER = "#FBFBFA"
_HAIRLINE = "#E9E8E4"
_ACCENT = "#1A7A54"
_ACCENT_WASH = "#EDF3EC"

_STYLE_BODY = (
    f"margin:0 auto;max-width:640px;padding:40px 20px 32px;background:{_PAPER};"
    f"font-family:{_SANS};color:{_BODY_TEXT};line-height:1.65;"
)
_STYLE_EYEBROW = (
    f"font-family:{_MONO};font-size:11px;font-weight:500;letter-spacing:0.18em;"
    f"text-transform:uppercase;color:{_MUTED};"
)
_STYLE_SECTION_LABEL = f"{_STYLE_EYEBROW}margin:44px 0 4px;"
_STYLE_META = f"font-family:{_MONO};font-size:11px;letter-spacing:0.06em;color:{_FAINT};"
_STYLE_LINK = f"color:{_INK};text-decoration:underline;text-decoration-color:{_HAIRLINE};"
_STYLE_RULE = f"border:none;border-top:1px solid {_HAIRLINE};margin:0;"


def _e(text: str) -> str:
    return html.escape(text, quote=True)


def _tag(text: str) -> str:
    return (
        f'<span style="font-family:{_MONO};font-size:10px;font-weight:500;'
        f"letter-spacing:0.1em;text-transform:uppercase;color:{_ACCENT};"
        f'background:{_ACCENT_WASH};border-radius:999px;padding:3px 10px;">{_e(text)}</span>'
    )


def render_html(digest: Digest, failed_feeds: list[str], issue_date: date) -> str:
    parts: list[str] = []
    parts.append(f'<div style="{_STYLE_BODY}">')

    # Masthead
    quiet_badge = f" &nbsp;{_tag('quiet week')}" if digest.quiet_week else ""
    parts.append(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td style="{_STYLE_EYEBROW}color:{_INK};">AI Reliability Weekly{quiet_badge}</td>'
        f'<td align="right" style="{_STYLE_META}">{issue_date.strftime("%b %d, %Y")}</td>'
        "</tr></table>"
        f'<hr style="{_STYLE_RULE}margin-top:12px;">'
    )

    # Headline + overview
    parts.append(
        f'<h1 style="font-family:{_SANS};font-size:30px;font-weight:700;'
        f"letter-spacing:-0.02em;line-height:1.15;color:{_INK};"
        f'margin:28px 0 14px;">{_e(digest.headline)}</h1>'
    )
    parts.append(
        f'<p style="font-size:17px;line-height:1.6;color:{_BODY_TEXT};margin:0 0 8px;">'
        f"{_e(digest.overview)}</p>"
    )

    if digest.top_stories:
        parts.append(f'<p style="{_STYLE_SECTION_LABEL}">Top stories</p>')
        for i, story in enumerate(digest.top_stories, start=1):
            rule = f'<hr style="{_STYLE_RULE}margin:24px 0 0;">' if i > 1 else ""
            parts.append(
                f"{rule}"
                '<div style="padding:24px 0 4px;">'
                f'<p style="{_STYLE_META}margin:0 0 6px;">'
                f"{i:02d} &middot; {_e(story.source)} &middot; {story.reading_minutes} min read</p>"
                f'<a href="{_e(story.link)}" style="{_STYLE_LINK}font-weight:600;'
                f'font-size:19px;letter-spacing:-0.01em;line-height:1.3;">{_e(story.title)}</a>'
                f'<p style="margin:10px 0 10px;color:{_BODY_TEXT};">{_e(story.summary)}</p>'
                f'<p style="margin:0 0 4px;">'
                f'<span style="{_STYLE_EYEBROW}font-size:10px;color:{_ACCENT};">Why it matters</span>'
                f'<br>{_e(story.why_it_matters)}</p>'
                "</div>"
            )

    if digest.quick_hits:
        parts.append(f'<p style="{_STYLE_SECTION_LABEL}margin-bottom:8px;">Quick hits</p>')
        for hit in digest.quick_hits:
            parts.append(
                f'<div style="border-top:1px solid {_HAIRLINE};padding:12px 0;">'
                f'<a href="{_e(hit.link)}" style="{_STYLE_LINK}font-weight:600;">{_e(hit.title)}</a>'
                f'<span style="{_STYLE_META}"> &middot; {_e(hit.source)}</span><br>'
                f'<span style="color:{_MUTED};">{_e(hit.one_liner)}</span></div>'
            )

    if digest.trends:
        parts.append(f'<p style="{_STYLE_SECTION_LABEL}margin-bottom:8px;">Trends this week</p>')
        for trend in digest.trends:
            parts.append(
                f'<p style="margin:0 0 12px;border-left:2px solid {_ACCENT};padding-left:14px;">'
                f'<strong style="color:{_INK};">{_e(trend.name)}</strong><br>'
                f'<span style="color:{_MUTED};">{_e(trend.evidence)}</span></p>'
            )

    if digest.career_implications:
        parts.append(f'<p style="{_STYLE_SECTION_LABEL}margin-bottom:8px;">For your career</p>')
        parts.append('<ol style="padding-left:22px;margin:0;">')
        for takeaway in digest.career_implications:
            parts.append(f'<li style="margin:0 0 10px;color:{_BODY_TEXT};">{_e(takeaway)}</li>')
        parts.append("</ol>")

    # Footer
    parts.append(f'<hr style="{_STYLE_RULE}margin:44px 0 14px;">')
    if failed_feeds:
        parts.append(
            f'<p style="{_STYLE_META}margin:0 0 8px;">Feeds unreachable this week: '
            f"{_e(', '.join(failed_feeds))}</p>"
        )
    parts.append(
        f'<p style="{_STYLE_META}margin:0;">Generated automatically &middot; '
        "curated for the AI Reliability &amp; Test Automation role</p>"
    )
    parts.append("</div>")
    return "\n".join(parts)


def subject_line(digest: Digest, issue_date: date) -> str:
    prefix = "AI Reliability Weekly"
    quiet = " (quiet week)" if digest.quiet_week else ""
    return f"{prefix} · {issue_date.strftime('%b %d')}{quiet} — {digest.headline}"
