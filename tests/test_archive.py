"""Archive stage: issue files and index generation."""
from __future__ import annotations

from datetime import date

from digest.archive import normalize_link, published_links, save_issue

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


def test_normalize_link_folds_cosmetic_url_differences():
    canonical = normalize_link("https://www.anthropic.com/engineering/infrastructure-noise")
    variants = [
        "http://www.anthropic.com/engineering/infrastructure-noise",  # scheme
        "https://anthropic.com/engineering/infrastructure-noise",  # no www.
        "https://www.anthropic.com/engineering/infrastructure-noise/",  # trailing slash
        "https://www.anthropic.com/engineering/infrastructure-noise?utm_source=rss",
        "https://www.anthropic.com/engineering/infrastructure-noise?ref=feed",
        "  https://www.anthropic.com/engineering/infrastructure-noise  ",
    ]
    for variant in variants:
        assert normalize_link(variant) == canonical, variant


def test_normalize_link_keeps_meaningful_query_and_distinct_paths():
    assert normalize_link("https://arxiv.org/abs/2608.20627") != normalize_link(
        "https://arxiv.org/abs/2608.20513"
    )
    # A query that identifies the resource must survive.
    assert "id=42" in normalize_link("https://example.com/post?id=42&utm_medium=email")


def test_normalize_link_rejects_relative_urls():
    assert normalize_link("2026-08-24.html") == ""
    assert normalize_link("") == ""


def test_published_links_reads_back_every_archived_article(tmp_path):
    save_issue(
        '<div><h1>Week one</h1>'
        '<a href="https://www.anthropic.com/engineering/infrastructure-noise">A</a>'
        '<a href="https://arxiv.org/abs/2608.20627">B</a></div>',
        date(2026, 8, 24),
        archive_dir=tmp_path,
    )
    save_issue(
        '<div><h1>Week two</h1><a href="https://example.com/c">C</a></div>',
        date(2026, 8, 31),
        archive_dir=tmp_path,
    )
    links = published_links(tmp_path)
    assert links == {
        "anthropic.com/engineering/infrastructure-noise",
        "arxiv.org/abs/2608.20627",
        "example.com/c",
    }
    # index.html links to issue files; those must not count as published articles.
    assert not any(link.endswith(".html") for link in links)


def test_published_links_on_a_missing_archive_is_empty(tmp_path):
    assert published_links(tmp_path / "nope") == set()
