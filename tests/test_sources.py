import json
from pathlib import Path

from remote_jobs.sources import remoteok, remotive, weworkremotely

FIX = Path(__file__).parent / "fixtures"


def test_remoteok_skips_legal_notice_and_parses_fields():
    jobs = remoteok.parse(json.loads((FIX / "remoteok.json").read_text(encoding="utf-8")))
    assert [j.title for j in jobs] == ["Automation Engineer", "Technical Writer"]
    first = jobs[0]
    assert first.source == "remoteok"
    assert first.company == "Acme Robotics"
    assert first.salary == "$60,000 - $90,000"
    assert first.tags == ["python", "automation", "n8n"]
    assert first.posted_at == "2026-10-16"
    assert first.description == "We automate boring work. Build pipelines with Python."
    # epoch fallback and empty salary
    assert jobs[1].salary == ""
    assert jobs[1].posted_at == "2025-10-09"


def test_remotive_parses_category_into_tags():
    jobs = remotive.parse(json.loads((FIX / "remotive.json").read_text(encoding="utf-8")))
    assert len(jobs) == 2
    ai = jobs[0]
    assert ai.source == "remotive"
    assert ai.tags == ["Software Development", "llm", "rag", "python"]
    assert ai.posted_at == "2026-10-15"
    assert ai.salary == "$80k - $120k"
    assert jobs[1].location == "USA"


def test_weworkremotely_splits_company_from_title():
    jobs = weworkremotely.parse((FIX / "weworkremotely.xml").read_text(encoding="utf-8"))
    assert len(jobs) == 2
    first = jobs[0]
    assert (first.company, first.title) == ("Scrapewise", "Data Extraction Specialist")
    assert first.tags == ["Programming", "Full-Time"]
    assert first.posted_at == "2026-10-16"
    assert first.description.startswith("Scrape websites")
    assert jobs[1].company == "" and jobs[1].title == "No Colon Title Here"
