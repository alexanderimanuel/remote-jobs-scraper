from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

from .models import FIELDS, Job


def write_csv(jobs: list[Job], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for job in jobs:
            w.writerow(job.to_row())


def write_json(jobs: list[Job], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [job.to_row() | {"tags": job.tags} for job in jobs]
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def print_table(jobs: list[Job], limit: int = 20, file=sys.stdout) -> None:
    """Compact terminal preview: date, source, title, company."""
    shown = jobs[:limit]
    if not shown:
        print("No jobs matched.", file=file)
        return
    w_title = min(max(len(j.title) for j in shown), 48)
    w_company = min(max(len(j.company) for j in shown), 24)
    for j in shown:
        title = (j.title[: w_title - 1] + "…") if len(j.title) > w_title else j.title
        company = (j.company[: w_company - 1] + "…") if len(j.company) > w_company else j.company
        print(f"{j.posted_at or '          ':10}  {j.source:<14}  {title:<{w_title}}  {company:<{w_company}}", file=file)
    if len(jobs) > limit:
        print(f"... and {len(jobs) - limit} more", file=file)
