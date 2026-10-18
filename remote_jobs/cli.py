from __future__ import annotations

import argparse
import logging
import sys
from datetime import date, timedelta

from .export import print_table, write_csv, write_json
from .http import make_session
from .models import Job
from .normalize import dedupe, matches_keywords, newer_than
from .sources import SOURCES

log = logging.getLogger("remote_jobs")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="remote_jobs",
        description="Collect remote job postings from RemoteOK, Remotive and We Work Remotely into one CSV or JSON file.",
    )
    p.add_argument("-k", "--keyword", action="append", default=[], metavar="WORD",
                   help="keep jobs whose title, company, tags or description contain WORD (repeatable, case-insensitive)")
    p.add_argument("--title-only", action="store_true",
                   help="match keywords against the title and tags only, not the description (fewer false positives)")
    p.add_argument("-s", "--source", action="append", choices=sorted(SOURCES), default=[],
                   help="only pull from this source (repeatable). Default: all sources")
    p.add_argument("--since-days", type=int, default=None, metavar="N",
                   help="only jobs posted in the last N days (jobs with unknown dates are kept)")
    p.add_argument("-o", "--out", default="jobs.csv", help="output file (default: jobs.csv)")
    p.add_argument("-f", "--format", choices=["csv", "json"], default=None,
                   help="output format; inferred from --out extension when omitted")
    p.add_argument("--limit", type=int, default=None, help="stop after this many jobs")
    p.add_argument("--no-preview", action="store_true", help="do not print the preview table")
    p.add_argument("-v", "--verbose", action="store_true", help="show per-source progress and retries")
    return p


def collect(sources: list[str], keywords: list[str], since_days: int | None, limit: int | None,
            fetchers=None, title_only: bool = False) -> list[Job]:
    """Pull, filter, de-duplicate and sort. `fetchers` can be injected for tests."""
    fetchers = fetchers or SOURCES
    session = make_session()
    all_jobs: list[Job] = []
    for name in sources:
        try:
            jobs = fetchers[name](session)
        except Exception as exc:  # one broken source must not kill the run
            log.error("%s: failed (%s), skipping", name, exc)
            continue
        log.info("%s: %d jobs", name, len(jobs))
        all_jobs.extend(jobs)

    since_date = (date.today() - timedelta(days=since_days)).isoformat() if since_days else None
    kept = [j for j in dedupe(all_jobs)
            if matches_keywords(j, keywords, title_only=title_only) and newer_than(j, since_date)]
    kept.sort(key=lambda j: (j.posted_at or "0000-00-00"), reverse=True)
    if limit:
        kept = kept[:limit]
    return kept


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")

    sources = args.source or sorted(SOURCES)
    fmt = args.format or ("json" if args.out.lower().endswith(".json") else "csv")

    jobs = collect(sources, args.keyword, args.since_days, args.limit, title_only=args.title_only)

    (write_json if fmt == "json" else write_csv)(jobs, args.out)
    if not args.no_preview:
        print_table(jobs)
    print(f"\n{len(jobs)} jobs written to {args.out} (sources: {', '.join(sources)}"
          f"{'; keywords: ' + ', '.join(args.keyword) if args.keyword else ''})", file=sys.stderr)
    return 0
