"""Persist each issue into archive/ and keep its indexes up to date.

Two indexes are maintained: README.md for browsing the folder on GitHub,
and index.html — the GitHub Pages front page, styled to match the email
(warm monochrome, one emerald accent, mono tracked-caps meta).
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parents[2] / "archive"

_TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)

_SANS = "-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif"
_MONO = "'SF Mono',SFMono-Regular,'Roboto Mono',Consolas,monospace"

_INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Reliability Weekly — Archive</title>
<style>
  body {{ margin:0 auto; max-width:640px; padding:48px 20px; background:#FBFBFA;
         font-family:{sans}; color:#37373D; line-height:1.65; }}
  .eyebrow {{ font-family:{mono}; font-size:11px; font-weight:500; letter-spacing:0.18em;
              text-transform:uppercase; color:#111113; margin:0; }}
  h1 {{ font-size:30px; font-weight:700; letter-spacing:-0.02em; line-height:1.15;
        color:#111113; margin:26px 0 8px; }}
  .sub {{ color:#6E6E76; margin:0 0 40px; }}
  hr {{ border:none; border-top:1px solid #E9E8E4; margin:12px 0 0; }}
  .issue {{ border-top:1px solid #E9E8E4; padding:16px 0; }}
  .issue a {{ color:#111113; text-decoration:underline; text-decoration-color:#E9E8E4;
              font-weight:600; font-size:17px; letter-spacing:-0.01em; }}
  .issue a:hover {{ color:#1A7A54; text-decoration-color:#1A7A54; }}
  .date {{ font-family:{mono}; font-size:11px; letter-spacing:0.06em; color:#9A9AA1;
           display:block; margin-bottom:4px; }}
  .footer {{ font-family:{mono}; font-size:11px; letter-spacing:0.06em; color:#9A9AA1;
             margin-top:44px; }}
</style>
</head>
<body>
<p class="eyebrow">AI Reliability Weekly</p>
<hr>
<h1>Issue archive</h1>
<p class="sub">A weekly analyst briefing on AI reliability and test automation,
curated from ~45 engineering feeds.</p>
{issues}
<p class="footer">Generated automatically &middot; newest first</p>
</body>
</html>
"""


def _issue_title(html_body: str) -> str:
    match = _TITLE_RE.search(html_body)
    return html.unescape(match.group(1)).strip() if match else "Weekly digest"


def save_issue(html_body: str, issue_date: date, archive_dir: Path | None = None) -> Path:
    """Write the issue HTML and regenerate both indexes. Returns the issue path."""
    directory = archive_dir or ARCHIVE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    issue_path = directory / f"{issue_date.isoformat()}.html"
    issue_path.write_text(html_body)
    _write_indexes(directory)
    return issue_path


def _issues(directory: Path) -> list[tuple[str, str]]:
    """(stem, title) per issue, newest first. index.html is not an issue."""
    return [
        (path.stem, _issue_title(path.read_text()))
        for path in sorted(directory.glob("*.html"), reverse=True)
        if path.name != "index.html"
    ]


def _write_indexes(directory: Path) -> None:
    issues = _issues(directory)

    md_lines = ["# Digest archive", ""]
    md_lines += [f"- [{stem} — {title}]({stem}.html)" for stem, title in issues]
    (directory / "README.md").write_text("\n".join(md_lines) + "\n")

    entries = "\n".join(
        f'<div class="issue"><span class="date">{stem}</span>'
        f'<a href="{stem}.html">{html.escape(title)}</a></div>'
        for stem, title in issues
    )
    (directory / "index.html").write_text(
        _INDEX_TEMPLATE.format(sans=_SANS, mono=_MONO, issues=entries)
    )
