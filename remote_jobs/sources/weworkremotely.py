"""We Work Remotely RSS feed: https://weworkremotely.com/remote-jobs.rss

Each <item> has <title>Company: Job title</title>, <link>, <pubDate>, <region>, <category>,
<type> and an HTML <description>. Parsed with the standard library, no feedparser needed.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET

import requests

from ..http import get
from ..models import Job
from ..normalize import strip_html, to_iso_date, truncate

URL = "https://weworkremotely.com/remote-jobs.rss"
NAME = "weworkremotely"


def _text(item: ET.Element, tag: str) -> str:
    el = item.find(tag)
    return (el.text or "").strip() if el is not None and el.text else ""


def split_title(raw: str) -> tuple[str, str]:
    """'Acme Inc: Senior Backend Engineer' -> ('Acme Inc', 'Senior Backend Engineer')."""
    if ":" in raw:
        company, title = raw.split(":", 1)
        return company.strip(), title.strip()
    return "", raw.strip()


def parse(xml_text: str) -> list[Job]:
    root = ET.fromstring(xml_text)
    jobs: list[Job] = []
    for item in root.iter("item"):
        company, title = split_title(_text(item, "title"))
        if not title:
            continue
        tags = [t for t in (_text(item, "category"), _text(item, "type")) if t]
        jobs.append(
            Job(
                source=NAME,
                title=title,
                company=company,
                url=_text(item, "link"),
                location=_text(item, "region") or "Anywhere in the World",
                salary="",
                tags=tags,
                posted_at=to_iso_date(_text(item, "pubDate")),
                description=truncate(strip_html(_text(item, "description"))),
            )
        )
    return jobs


def fetch(session: requests.Session) -> list[Job]:
    resp = get(session, URL)
    return parse(resp.text)
