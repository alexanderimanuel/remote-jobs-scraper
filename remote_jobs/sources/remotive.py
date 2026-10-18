"""Remotive public API: https://remotive.com/api/remote-jobs

Response: {"job-count": N, "jobs": [{"id": 1, "url": "...", "title": "...", "company_name": "...",
 "category": "...", "tags": [...], "job_type": "full_time", "publication_date": "2026-10-16T08:00:00",
 "candidate_required_location": "Worldwide", "salary": "$80k - $120k", "description": "<p>html</p>"}]}
"""
from __future__ import annotations

import requests

from ..http import get
from ..models import Job
from ..normalize import strip_html, to_iso_date, truncate

URL = "https://remotive.com/api/remote-jobs"
NAME = "remotive"


def parse(payload: dict) -> list[Job]:
    jobs: list[Job] = []
    for item in payload.get("jobs") or []:
        if not isinstance(item, dict) or not item.get("title"):
            continue
        tags = [str(t).strip() for t in item.get("tags") or [] if str(t).strip()]
        if item.get("category"):
            tags.insert(0, str(item["category"]).strip())
        jobs.append(
            Job(
                source=NAME,
                title=item["title"].strip(),
                company=(item.get("company_name") or "").strip(),
                url=(item.get("url") or "").strip(),
                location=(item.get("candidate_required_location") or "Worldwide").strip(),
                salary=(item.get("salary") or "").strip(),
                tags=tags,
                posted_at=to_iso_date(item.get("publication_date")),
                description=truncate(strip_html(item.get("description"))),
            )
        )
    return jobs


def fetch(session: requests.Session) -> list[Job]:
    resp = get(session, URL)
    return parse(resp.json())
