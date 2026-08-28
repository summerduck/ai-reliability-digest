"""Render a Digest into an HTML email body.

Design language: anthropic.com editorial — warm paper, serif body, bold sans display.
- Ink #141413 on ivory #FAF9F5 (both sampled from anthropic.com); never pure black/white.
- Body copy is a Tiempos-style serif (Georgia fallback); headlines are large,
  heavy, tight-tracked sans (Styrene fallback stack).
- One accent, olive #788C5D (their artwork green), carries the why-it-matters
  label, trend bars, and state; #5C6F45 is its darker text-safe shade.
- No cards or shadows: sections and stories separate on 1px #E8E6DC hairlines.
- Meta text (section labels, story numbers, reading time) stays small
  tracked-caps monospace.
Email-safe: inline styles only, system font stacks, no images or scripts.
Sized to read well full-page on an iPad too: 680px measure, 18px serif body.
"""
from __future__ import annotations

import html
from datetime import date

from .models import Digest

_SANS = "'Styrene A',-apple-system,'Helvetica Neue','Segoe UI',Roboto,Arial,sans-serif"
_SERIF = "'Tiempos Text','Iowan Old Style',Georgia,'Times New Roman',serif"
_MONO = "'SF Mono',SFMono-Regular,'Roboto Mono',Consolas,monospace"

_INK = "#141413"
_BODY_TEXT = "#141413"
_MUTED = "#6F6E69"
_FAINT = "#95948E"
_PAPER = "#FAF9F5"
_HAIRLINE = "#E8E6DC"
_ACCENT = "#788C5D"
_ACCENT_TEXT = "#5C6F45"
_ACCENT_WASH = "#EDEFE3"

_STYLE_BODY = (
    f"margin:0 auto;max-width:680px;padding:48px 24px 36px;background:{_PAPER};"
    f"font-family:{_SERIF};color:{_BODY_TEXT};font-size:18px;line-height:1.7;"
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
        f"letter-spacing:0.1em;text-transform:uppercase;color:{_ACCENT_TEXT};"
        f'background:{_ACCENT_WASH};border-radius:999px;padding:3px 10px;">{_e(text)}</span>'
    )


def render_html(digest: Digest, failed_feeds: list[str], issue_date: date) -> str:
    parts: list[str] = []
    parts.append(f'<div style="{_STYLE_BODY}">')

    # Masthead
    quiet_badge = f" &nbsp;{_tag('quiet week')}" if digest.quiet_week else ""
    parts.append(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0">'
        f'<tr><td style="font-family:{_SANS};font-size:15px;font-weight:700;'
        f'letter-spacing:-0.01em;color:{_INK};">AI Reliability Weekly{quiet_badge}</td>'
        f'<td align="right" style="{_STYLE_META}">{issue_date.strftime("%b %d, %Y")}</td>'
        "</tr></table>"
        f'<hr style="{_STYLE_RULE}margin-top:12px;">'
    )

    # Headline + overview
    parts.append(
        f'<h1 style="font-family:{_SANS};font-size:40px;font-weight:700;'
        f"letter-spacing:-0.025em;line-height:1.1;color:{_INK};"
        f'margin:36px 0 18px;">{_e(digest.headline)}</h1>'
    )
    parts.append(
        f'<p style="font-size:21px;line-height:1.5;color:{_BODY_TEXT};margin:0 0 8px;">'
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
                f'<a href="{_e(story.link)}" style="{_STYLE_LINK}font-family:{_SANS};'
                f"font-weight:700;font-size:22px;letter-spacing:-0.015em;"
                f'line-height:1.25;">{_e(story.title)}</a>'
                f'<p style="margin:10px 0 10px;color:{_BODY_TEXT};">{_e(story.summary)}</p>'
                f'<p style="margin:0 0 4px;">'
                f'<span style="{_STYLE_EYEBROW}font-size:10px;color:{_ACCENT_TEXT};">'
                "Why it matters</span>"
                f'<br>{_e(story.why_it_matters)}</p>'
                "</div>"
            )

    if digest.quick_hits:
        parts.append(f'<p style="{_STYLE_SECTION_LABEL}margin-bottom:8px;">Quick hits</p>')
        for hit in digest.quick_hits:
            parts.append(
                f'<div style="border-top:1px solid {_HAIRLINE};padding:12px 0;">'
                f'<a href="{_e(hit.link)}" style="{_STYLE_LINK}font-family:{_SANS};'
                f'font-weight:600;font-size:17px;">{_e(hit.title)}</a>'
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
