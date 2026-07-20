# Remote Job Board Aggregator

Monitors [RemoteOK](https://remoteok.com)'s public job API for new
listings matching your keywords, deduplicates against previously seen
jobs, and logs matches. Built to run automatically via GitHub Actions
— no server required.

## New techniques in this project (vs. HTML scraping)

1. **API-first approach** — RemoteOK exposes a public JSON API
   (`remoteok.com/api`). No HTML parsing, no Playwright, no broken
   selectors when the site redesigns. Always check for a public API
   before reaching for a scraper — it's faster and far more stable.
2. **Automated tests (`pytest`)** — the filtering and deduplication
   logic is tested against fake data, not the live API, so tests run
   fast and never break because of network issues.
3. **GitHub Actions scheduling** — replaces cron/a VPS entirely.
   GitHub runs this on a schedule using their infrastructure, for
   free within normal usage limits.
4. **Environment-based config** — keywords are set via an environment
   variable (`JOB_KEYWORDS`), not hardcoded, so the same code works
   locally and in CI without edits.

## Project structure

```
remote-job-monitor/
├── src/
│   └── aggregator.py       # main pipeline
├── tests/
│   └── test_aggregator.py  # pytest suite
├── .github/workflows/
│   └── run-aggregator.yml  # scheduled GitHub Actions job
├── requirements.txt
├── .gitignore
└── README.md
```

## Run locally

```bash
pip install -r requirements.txt
export JOB_KEYWORDS="python,django,fastapi"
python src/aggregator.py
```

## Run tests

```bash
pytest tests/ -v
```

## Deploy to GitHub (so it runs automatically)

1. Create a new empty repo on GitHub (don't initialize with a README)
2. From this project folder:
   ```bash
   git add .
   git commit -m "Initial commit: remote job aggregator"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/remote-job-monitor.git
   git push -u origin main
   ```
3. Go to your repo → **Settings → Actions → General** → under
   "Workflow permissions" select **"Read and write permissions"**
   (needed so the workflow can commit `jobs.db` back to the repo)
4. That's it — the workflow will now run daily at 08:00 UTC
   automatically. You can also trigger it manually from the
   **Actions** tab → "Job Aggregator" → "Run workflow"

## Customize keywords without touching code

Edit the `JOB_KEYWORDS` line in
`.github/workflows/run-aggregator.yml`, or better, set it as a
[GitHub Actions variable](https://docs.github.com/en/actions/learn-github-actions/variables)
so non-developers on a team could update it without editing YAML.

## Extending this for a real client

- Swap the logging line for a Slack webhook call on `[NEW MATCH]`
- Add more job sources (many boards have similar public/semi-public
  APIs — always check before scraping HTML)
- Add salary/location filtering using the extra fields RemoteOK
  returns per job
- Export matches to a Google Sheet via their API for non-technical
  stakeholders to review

## Why this project is a stronger portfolio piece than a pure scraper

It shows you know when *not* to build a scraper — recognizing and
using an existing API is a genuine differentiator that separates
freelancers who understand the tradeoffs from ones who reach for
Playwright by default. It's also fully reproducible and testable,
which real engineering teams and technical clients notice and value.
# remote-job-monitor
# remote-job-monitor
