"""Persist each issue into archive/ and keep its indexes up to date.

Issues are stored as full HTML documents: the email body wrapped in a shell
with a viewport meta so they read well in a tablet/phone browser, not at the
980px legacy zoom Safari applies to headerless pages.

Two indexes are maintained: README.md for browsing the folder on GitHub,
and index.html — the GitHub Pages front page, styled to match the email
(anthropic.com palette: ivory paper, ink, one olive accent).
"""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parents[2] / "archive"

_TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)

_SANS = "'Styrene A',-apple-system,'Helvetica Neue','Segoe UI',Roboto,Arial,sans-serif"
_SERIF = "'Tiempos Text','Iowan Old Style',Georgia,'Times New Roman',serif"
_MONO = "'SF Mono',SFMono-Regular,'Roboto Mono',Consolas,monospace"

_ISSUE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} — AI Reliability Weekly</title>
<style>body {{ margin:0; background:#FAF9F5; }}</style>
</head>
<body>
{body}
</body>
</html>
"""

_INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AI Reliability Weekly — Archive</title>
<style>
  body {{ margin:0 auto; max-width:680px; padding:48px 24px; background:#FAF9F5;
         font-family:{serif}; color:#141413; font-size:18px; line-height:1.7; }}
  .masthead {{ font-family:{sans}; font-size:15px; font-weight:700;
               letter-spacing:-0.01em; color:#141413; margin:0; }}
  h1 {{ font-family:{sans}; font-size:40px; font-weight:700; letter-spacing:-0.025em;
        line-height:1.1; color:#141413; margin:34px 0 10px; }}
  .sub {{ font-size:21px; line-height:1.5; color:#141413; margin:0 0 44px; }}
  hr {{ border:none; border-top:1px solid #E8E6DC; margin:12px 0 0; }}
  .issue {{ border-top:1px solid #E8E6DC; padding:18px 0; }}
  .issue a {{ font-family:{sans}; color:#141413; text-decoration:underline;
              text-decoration-color:#E8E6DC; font-weight:600; font-size:19px;
              letter-spacing:-0.015em; }}
  .issue a:hover {{ color:#5C6F45; text-decoration-color:#788C5D; }}
  .date {{ font-family:{mono}; font-size:11px; letter-spacing:0.06em; color:#95948E;
           display:block; margin-bottom:4px; }}
  .footer {{ font-family:{mono}; font-size:11px; letter-spacing:0.06em; color:#95948E;
             margin-top:44px; }}
</style>
</head>
<body>
<p class="masthead">AI Reliability Weekly</p>
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
    issue_path.write_text(
        _ISSUE_TEMPLATE.format(title=_issue_title(html_body), body=html_body)
    )
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
        _INDEX_TEMPLATE.format(sans=_SANS, serif=_SERIF, mono=_MONO, issues=entries)
    )
