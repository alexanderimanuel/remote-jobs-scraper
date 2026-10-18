from __future__ import annotations

import logging
import time

import requests

from . import __version__

log = logging.getLogger(__name__)

USER_AGENT = f"remote-jobs-scraper/{__version__} (+https://github.com/alexanderimanuel/remote-jobs-scraper)"
DEFAULT_TIMEOUT = 20
RETRIES = 3
BACKOFF_SECONDS = 2.0


def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Accept": "*/*"})
    return s


def get(session: requests.Session, url: str, **kwargs) -> requests.Response:
    """GET with a small retry loop. Raises the last error if every attempt fails."""
    kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
    last_exc: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = session.get(url, **kwargs)
            if resp.status_code >= 500 or resp.status_code == 429:
                raise requests.HTTPError(f"HTTP {resp.status_code} for {url}", response=resp)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:  # network, timeout, HTTP error
            last_exc = exc
            if attempt < RETRIES:
                wait = BACKOFF_SECONDS * attempt
                log.warning("attempt %d/%d failed for %s (%s); retrying in %.0fs", attempt, RETRIES, url, exc, wait)
                time.sleep(wait)
    assert last_exc is not None
    raise last_exc
