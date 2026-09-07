"""Archive stage: issue files and index generation."""
from __future__ import annotations

from datetime import date

from digest.archive import save_issue

HTML_A = '<div><h1 style="x">Evals week</h1><p>body</p></div>'
HTML_B = "<div><h1>Agents &amp; RAG</h1><p>body</p></div>"


def test_issue_written_as_full_document(tmp_path):
    path = save_issue(HTML_A, date(2026, 8, 17), archive_dir=tmp_path)
    assert path == tmp_path / "2026-08-17.html"
    saved = path.read_text()
    assert HTML_A in saved  # the email body, verbatim
    # Wrapped in a real document so tablet/phone browsers don't legacy-zoom it.
    assert saved.startswith("<!doctype html>")
    assert 'name="viewport"' in saved
    assert "<title>Evals week — AI Reliability Weekly</title>" in saved


def test_index_lists_issues_newest_first_with_titles(tmp_path):
    save_issue(HTML_A, date(2026, 8, 17), archive_dir=tmp_path)
    save_issue(HTML_B, date(2026, 8, 24), archive_dir=tmp_path)
    index = (tmp_path / "README.md").read_text()
    assert index.index("2026-08-24") < index.index("2026-08-17")
    assert "[2026-08-17 — Evals week](2026-08-17.html)" in index
    assert "Agents & RAG" in index


def test_pages_index_lists_issues_and_ignores_itself(tmp_path):
    save_issue(HTML_A, date(2026, 8, 17), archive_dir=tmp_path)
    save_issue(HTML_B, date(2026, 8, 24), archive_dir=tmp_path)
    index = (tmp_path / "index.html").read_text()
    assert '<a href="2026-08-17.html">Evals week</a>' in index
    assert "Agents &amp; RAG" in index
    assert index.index("2026-08-24") < index.index("2026-08-17")
    # A rerun must not list index.html as an issue.
    save_issue(HTML_A, date(2026, 8, 17), archive_dir=tmp_path)
    assert "index.html" not in (tmp_path / "README.md").read_text()
    assert 'href="index.html"' not in (tmp_path / "index.html").read_text()


def test_rerun_same_date_overwrites_without_duplicate_index_entry(tmp_path):
    save_issue(HTML_A, date(2026, 8, 17), archive_dir=tmp_path)
    save_issue(HTML_B, date(2026, 8, 17), archive_dir=tmp_path)
    index = (tmp_path / "README.md").read_text()
    assert index.count("- [2026-08-17") == 1
    saved = (tmp_path / "2026-08-17.html").read_text()
    assert HTML_B in saved
    assert HTML_A not in saved
