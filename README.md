# remote-jobs-scraper

Collect remote job postings from **RemoteOK**, **Remotive** and **We Work Remotely** into one clean CSV or JSON file, filtered by keyword, de-duplicated and sorted by date.

I built this because checking three job boards every morning by hand is exactly the kind of manual work a script should do. It is also a small, honest example of how I approach scraping work: public feeds first, polite requests with retries, a normalised schema, tests with fixtures, and a scheduled run that keeps a live sample in the repo.

[![tests](https://github.com/alexanderimanuel/remote-jobs-scraper/actions/workflows/ci.yml/badge.svg)](https://github.com/alexanderimanuel/remote-jobs-scraper/actions/workflows/ci.yml)

## Run it in three commands

```bash
git clone https://github.com/alexanderimanuel/remote-jobs-scraper.git && cd remote-jobs-scraper
pip install -e .
python -m remote_jobs -k ai -k automation -k "technical writer" --since-days 14 -o jobs.csv
```

Output (preview is printed to the terminal, the full table goes to `jobs.csv`):

```
2026-10-17  remoteok        Software Engineer AI Coding Tasks                 Askable
2026-10-17  weworkremotely  Principal Product Manager, Agentic AI             Legion
2026-10-16  remoteok        Associate Data Scientist                          AlgaeCal
2026-10-15  weworkremotely  Senior Python Developer (CRM - AI/LLM)            Emerging Travel Group
2026-10-15  weworkremotely  AI Experience Engineer (Conversational AI)        Upgrade
... and 32 more

37 jobs written to jobs.csv (sources: remoteok, remotive, weworkremotely; keywords: ai, automation, technical writer)
```

A real snapshot lives in [`data/sample.csv`](data/sample.csv) and [`data/sample.json`](data/sample.json). The `daily jobs snapshot` workflow refreshes `data/latest.csv` every morning.

## What you get

Every job, whatever the source, is normalised to the same nine columns:

| column        | example                                             |
|---------------|-----------------------------------------------------|
| `source`      | `remoteok`, `remotive`, `weworkremotely`             |
| `title`       | `AI Experience Engineer (Conversational AI)`        |
| `company`     | `Upgrade`                                            |
| `location`    | `Worldwide`, `Europe Only`, `USA`                    |
| `salary`      | `$80,000 - $120,000` (empty when the board has none) |
| `tags`        | `python, llm, rag`                                   |
| `posted_at`   | `2026-10-15` (ISO date)                              |
| `url`         | link to the original posting                         |
| `description` | first 400 characters as plain text                   |

Duplicates are removed by canonical URL (query strings, fragments and trailing slashes ignored), and results are sorted newest first.

## Options

```
python -m remote_jobs --help

  -k, --keyword WORD   keep jobs whose title, company, tags or description contain WORD
                       (repeatable; matches at the start of a word, so "ai" hits "AI-powered" but not "retail")
  --title-only         match keywords against title and tags only (fewer false positives)
  -s, --source NAME    remoteok | remotive | weworkremotely (repeatable; default: all)
  --since-days N       only jobs posted in the last N days
  -o, --out FILE       jobs.csv (default) or anything ending in .json
  -f, --format         csv | json (inferred from --out when omitted)
  --limit N            stop after N jobs
  --no-preview         skip the terminal table
  -v, --verbose        per-source counts and retry messages
```

Examples:

```bash
# Only QA automation roles from the last week, as JSON
python -m remote_jobs -k "qa automation" -k "test automation" --title-only --since-days 7 -o qa.json

# Everything on RemoteOK, no filter
python -m remote_jobs -s remoteok -o remoteok.csv
```

## How it works

```
remote_jobs/
  cli.py          argparse entry point; collect() pulls, filters, de-dupes, sorts
  http.py         one Session with a descriptive User-Agent, timeouts and 3 retries with backoff
  models.py       Job dataclass: the single schema every source maps into
  normalize.py    HTML -> text, many date formats -> ISO, canonical URLs, keyword matching
  export.py       CSV / JSON writers and the terminal preview
  sources/
    remoteok.py        public JSON feed  (https://remoteok.com/api)
    remotive.py        public JSON API   (https://remotive.com/api/remote-jobs)
    weworkremotely.py  RSS feed, parsed with the standard library
```

Design choices:

- **Public feeds, not HTML scraping.** All three boards publish JSON or RSS. That is faster, more stable and respects the sites. The structure still shows how I would wrap an HTML source: one `parse()` that turns raw payload into `Job` objects, one `fetch()` that does the network call.
- **One broken source never kills the run.** Each fetcher is wrapped; a failure is logged and the other sources still produce output.
- **Tests run offline.** Fixtures in `tests/fixtures/` are real-shaped payloads, so parsing is tested without hitting the network.

## Adding a source

1. Create `remote_jobs/sources/<name>.py` with `parse(payload) -> list[Job]` and `fetch(session) -> list[Job]`.
2. Register it in `remote_jobs/sources/__init__.py`.
3. Drop a small fixture in `tests/fixtures/` and add a test.

That is usually 30 to 60 lines.

## Development

```bash
pip install -e ".[dev]"
pytest -q
```

## Notes on use

RemoteOK asks for attribution and a link back when their data is reused; the `url` column keeps every posting pointed at the original board. Please keep that if you build on this.

## Author

Alexander Imanuel Widjanarko, Malang, Indonesia. AI engineer and researcher; I build scrapers, automations and LLM integrations that replace manual work.
[alexiw.my.id](https://alexiw.my.id) · [LinkedIn](https://www.linkedin.com/in/alexander-imanuel-widjanarko) · [Google Scholar](https://scholar.google.com/citations?user=t97LgJ4AAAAJ&hl=en)

MIT License.
