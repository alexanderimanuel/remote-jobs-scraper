from __future__ import annotations

from typing import Callable

import requests

from ..models import Job
from . import remoteok, remotive, weworkremotely

Fetcher = Callable[[requests.Session], list[Job]]

SOURCES: dict[str, Fetcher] = {
    "remoteok": remoteok.fetch,
    "remotive": remotive.fetch,
    "weworkremotely": weworkremotely.fetch,
}
