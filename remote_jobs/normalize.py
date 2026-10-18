from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit

from .models import Job

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

DESCRIPTION_MAX = 400


def strip_html(text: str | None) -> str:
    """Turn an HTML fragment into one line of plain text."""
    if not text:
        return ""
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    return _WS_RE.sub(" ", text).strip()


def truncate(text: str, limit: int = DESCRIPTION_MAX) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def to_iso_date(value) -> str:
    """Accept epoch seconds, RFC 2822 or ISO 8601 strings; return YYYY-MM-DD or ''."""
    if value in (None, "", 0):
        return ""
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc).date().isoformat()
        s = str(value).strip()
        if s.isdigit():
            return datetime.fromtimestamp(float(s), tz=timezone.utc).date().isoformat()
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            return parsedate_to_datetime(s).date().isoformat()
    except (ValueError, TypeError, OverflowError):
        return ""


def canonical_url(url: str) -> str:
    """Lower-case host, drop query string and fragment, strip trailing slash. Used for de-duplication."""
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def dedupe(jobs: list[Job]) -> list[Job]:
    seen: set[str] = set()
    out: list[Job] = []
    for job in jobs:
        key = canonical_url(job.url) or (job.title.lower(), job.company.lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(job)
    return out


def keyword_pattern(keyword: str) -> re.Pattern:
    """Match the keyword at the start of a word, case-insensitive.

    'ai' matches 'AI', 'AI-powered' and 'ai/ml' but not 'retail' or 'maintain';
    'scrap' matches 'scraping' and 'scraper'; 'technical writer' matches as a phrase.
    """
    return re.compile(r"\b" + re.escape(keyword.strip().lower()), re.IGNORECASE)


def matches_keywords(job: Job, keywords: list[str], title_only: bool = False) -> bool:
    """True if any keyword appears (as a word prefix) in title, company, tags or description.

    With title_only=True only the title and tags are searched, which gives far fewer false positives
    (a sales job whose description mentions "AI" no longer counts).
    """
    if not keywords:
        return True
    text = job.searchable_text(title_only=title_only)
    return any(keyword_pattern(k).search(text) for k in keywords if k.strip())


def newer_than(job: Job, since_date: str | None) -> bool:
    if not since_date:
        return True
    if not job.posted_at:
        return True  # unknown date: keep it, better than silently dropping
    return job.posted_at >= since_date
