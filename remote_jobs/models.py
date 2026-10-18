from __future__ import annotations

from dataclasses import dataclass, field, asdict

FIELDS = [
    "source",
    "title",
    "company",
    "location",
    "salary",
    "tags",
    "posted_at",
    "url",
    "description",
]


@dataclass
class Job:
    """One job posting, normalised to the same shape regardless of source."""

    source: str
    title: str
    company: str
    url: str
    location: str = ""
    salary: str = ""
    tags: list[str] = field(default_factory=list)
    posted_at: str = ""  # ISO 8601 date (YYYY-MM-DD), empty if unknown
    description: str = ""  # plain text, truncated

    def to_row(self) -> dict:
        d = asdict(self)
        d["tags"] = ", ".join(self.tags)
        return {k: d[k] for k in FIELDS}

    def searchable_text(self, title_only: bool = False) -> str:
        parts = [self.title, " ".join(self.tags)]
        if not title_only:
            parts += [self.company, self.description]
        return " ".join(parts).lower()
