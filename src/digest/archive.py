"""Persist each issue into archive/ and keep its index up to date."""
from __future__ import annotations

import html
import re
from datetime import date
from pathlib import Path

ARCHIVE_DIR = Path(__file__).resolve().parents[2] / "archive"

_TITLE_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL)


def _issue_title(html_body: str) -> str:
    match = _TITLE_RE.search(html_body)
    return html.unescape(match.group(1)).strip() if match else "Weekly digest"


def save_issue(html_body: str, issue_date: date, archive_dir: Path | None = None) -> Path:
    """Write the issue HTML and regenerate the archive index. Returns the issue path."""
    directory = archive_dir or ARCHIVE_DIR
    directory.mkdir(parents=True, exist_ok=True)
    issue_path = directory / f"{issue_date.isoformat()}.html"
    issue_path.write_text(html_body)
    _write_index(directory)
    return issue_path


def _write_index(directory: Path) -> None:
    lines = ["# Digest archive", ""]
    for issue in sorted(directory.glob("*.html"), reverse=True):
        title = _issue_title(issue.read_text())
        lines.append(f"- [{issue.stem} — {title}]({issue.name})")
    (directory / "README.md").write_text("\n".join(lines) + "\n")
