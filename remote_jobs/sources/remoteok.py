"""RemoteOK public JSON feed: https://remoteok.com/api

The first element of the array is a legal notice, not a job. Each job looks like:
{"id": "...", "position": "...", "company": "...", "location": "...", "tags": [...],
 "salary_min": 50000, "salary_max": 90000, "url": "https://remoteok.com/remote-jobs/...",
 "date": "2026-10-16T10:11:12+00:00", "description": "<p>html</p>"}
"""
from __future__ import annotations

import requests

from ..http import get
from ..models import Job
from ..normalize import strip_html, to_iso_date, truncate

URL = "https://remoteok.com/api"
NAME = "remoteok"


def parse(payload: list) -> list[Job]:
    jobs: list[Job] = []
    for item in payload:
        if not isinstance(item, dict) or "position" not in item:
            continue  # skips the legal-notice element and anything malformed
        salary = ""
        lo, hi = item.get("salary_min"), item.get("salary_max")
        if lo and hi and int(lo) != int(hi):
            salary = f"${int(lo):,} - ${int(hi):,}"
        elif lo or hi:
            salary = f"${int(lo or hi):,}"
        jobs.append(
            Job(
                source=NAME,
                title=(item.get("position") or "").strip(),
                company=(item.get("company") or "").strip(),
                url=(item.get("url") or "").strip(),
                location=(item.get("location") or "Worldwide").strip(),
                salary=salary,
                tags=[str(t).strip() for t in item.get("tags") or [] if str(t).strip()],
                posted_at=to_iso_date(item.get("date") or item.get("epoch")),
                description=truncate(strip_html(item.get("description"))),
            )
        )
    return jobs


def fetch(session: requests.Session) -> list[Job]:
    resp = get(session, URL)
    return parse(resp.json())
