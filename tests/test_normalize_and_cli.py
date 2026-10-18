import csv
import json

from remote_jobs.cli import collect, main
from remote_jobs.models import Job
from remote_jobs.normalize import canonical_url, dedupe, matches_keywords, strip_html, to_iso_date


def job(**kw) -> Job:
    base = dict(source="test", title="Automation Engineer", company="Acme", url="https://x.io/j/1")
    base.update(kw)
    return Job(**base)


def test_strip_html_and_entities():
    assert strip_html("<p>Hello&nbsp;<b>world</b>&amp; co</p>") == "Hello world & co"
    assert strip_html(None) == ""


def test_to_iso_date_accepts_many_formats():
    assert to_iso_date("2026-10-16T10:11:12+00:00") == "2026-10-16"
    assert to_iso_date("Thu, 16 Oct 2026 09:30:00 +0000") == "2026-10-16"
    assert to_iso_date(1760000000) == "2025-10-09"
    assert to_iso_date("not a date") == ""
    assert to_iso_date(None) == ""


def test_canonical_url_ignores_query_and_case():
    assert canonical_url("HTTPS://RemoteOK.com/remote-jobs/1?ref=feed#top") == "https://remoteok.com/remote-jobs/1"


def test_dedupe_by_url():
    a = job(url="https://x.io/j/1?utm=a")
    b = job(url="https://x.io/j/1/")
    c = job(url="https://x.io/j/2")
    assert [j.url for j in dedupe([a, b, c])] == [a.url, c.url]


def test_keyword_matching_is_case_insensitive_and_searches_tags():
    j = job(title="Senior Engineer", tags=["LLM"], description="Build chatbots")
    assert matches_keywords(j, ["llm"])
    assert matches_keywords(j, ["CHATBOT"])
    assert not matches_keywords(j, ["kubernetes"])
    assert matches_keywords(j, [])  # no keywords means keep everything


def test_keyword_matches_word_prefix_not_substring():
    retail = job(title="Account Executive - Retail", description="maintain accounts")
    assert not matches_keywords(retail, ["ai"])  # 'ai' inside 'retail' / 'maintain' must not match
    assert matches_keywords(job(title="AI-powered search"), ["ai"])
    assert matches_keywords(job(title="Web Scraping Specialist"), ["scrap"])
    assert matches_keywords(job(title="Senior Technical Writer"), ["technical writer"])
    assert not matches_keywords(job(title="Technical Support Writer"), ["technical writer"])


def test_title_only_ignores_description_and_company():
    j = job(title="Account Executive", company="AI Corp", description="We sell AI tools")
    assert matches_keywords(j, ["ai"])
    assert not matches_keywords(j, ["ai"], title_only=True)
    assert matches_keywords(job(title="Engineer", tags=["ai"]), ["ai"], title_only=True)


def test_collect_survives_a_broken_source_and_filters(monkeypatch):
    def good(_session):
        return [job(title="AI Engineer", posted_at="2026-10-16"), job(title="Chef", url="https://x.io/j/9", posted_at="2026-10-01")]

    def broken(_session):
        raise RuntimeError("boom")

    jobs = collect(["good", "broken"], ["ai"], since_days=None, limit=None, fetchers={"good": good, "broken": broken})
    assert [j.title for j in jobs] == ["AI Engineer"]


def test_main_writes_csv_and_json(tmp_path, monkeypatch):
    import remote_jobs.cli as cli

    monkeypatch.setattr(cli, "SOURCES", {"fake": lambda _s: [job(tags=["python", "n8n"], posted_at="2026-10-16")]})
    out_csv = tmp_path / "jobs.csv"
    out_json = tmp_path / "jobs.json"

    assert main(["-s", "fake", "-o", str(out_csv), "--no-preview"]) == 0
    rows = list(csv.DictReader(out_csv.open(encoding="utf-8")))
    assert rows[0]["title"] == "Automation Engineer" and rows[0]["tags"] == "python, n8n"

    assert main(["-s", "fake", "-o", str(out_json), "--no-preview"]) == 0
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data[0]["tags"] == ["python", "n8n"]
