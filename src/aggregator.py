"""
Remote Job Board Aggregator
----------------------------
NEW TECHNIQUE: API-first scraping.

Instead of parsing HTML with BeautifulSoup/Playwright, this hits
RemoteOK's public JSON API directly. Always check if a site offers
this before reaching for a browser -- it's faster, more reliable,
and avoids HTML-parsing fragility entirely.

Pipeline:
1. Fetch job listings from the API
2. Filter by keyword (e.g. "python")
3. Deduplicate against what we've already seen (SQLite)
4. Log new matches (this is what a Slack/email alert would hook into)
"""

import os
import sqlite3
import logging
import requests
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

API_URL = "https://remoteok.com/api"
DB_PATH = os.getenv("DB_PATH", "jobs.db")
LOG_PATH = os.getenv("LOG_PATH", "aggregator.log")
KEYWORDS = os.getenv("JOB_KEYWORDS", "python").lower().split(",")

# RemoteOK asks that API consumers identify themselves with a real User-Agent
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobMonitorBot/1.0; +educational-project)"
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# API FETCH  (this replaces the whole scraping layer from the Allbirds project)
# ---------------------------------------------------------------------------

def fetch_jobs() -> list[dict]:
    """Hit the public API directly. No browser, no HTML parsing needed."""
    resp = requests.get(API_URL, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # RemoteOK's API returns a legal/metadata object as the first item --
    # skip it. This kind of quirk is common with public APIs; always
    # inspect real output before assuming a clean structure.
    jobs = [item for item in data if isinstance(item, dict) and "id" in item]
    logger.info("Fetched %d total job listings from API", len(jobs))
    return jobs


def filter_jobs(jobs: list[dict], keywords: list[str]) -> list[dict]:
    matched = []
    for job in jobs:
        haystack = " ".join(
            str(job.get(field, "")) for field in ("position", "description", "tags")
        ).lower()
        if any(kw.strip() in haystack for kw in keywords):
            matched.append(job)
    logger.info("Filtered to %d jobs matching keywords %s", len(matched), keywords)
    return matched


# ---------------------------------------------------------------------------
# DATABASE / DEDUPLICATION
# ---------------------------------------------------------------------------

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS seen_jobs (
            job_id TEXT PRIMARY KEY,
            position TEXT,
            company TEXT,
            url TEXT,
            first_seen_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def is_new_job(job_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,))
    exists = cur.fetchone() is not None
    conn.close()
    return not exists


def save_job(job: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO seen_jobs (job_id, position, company, url, first_seen_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            str(job.get("id")),
            job.get("position", "Unknown"),
            job.get("company", "Unknown"),
            job.get("url", ""),
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------------------------

def main():
    logger.info("=== Starting job aggregator run (keywords=%s) ===", KEYWORDS)
    init_db()

    try:
        jobs = fetch_jobs()
    except requests.RequestException as e:
        logger.error("Failed to fetch from API: %s", e)
        return

    matched = filter_jobs(jobs, KEYWORDS)

    new_count = 0
    for job in matched:
        job_id = str(job.get("id"))
        if is_new_job(job_id):
            new_count += 1
            logger.info(
                "[NEW MATCH] %s at %s — %s",
                job.get("position"), job.get("company"), job.get("url"),
            )
            save_job(job)

    logger.info("=== Run complete: %d new matches out of %d filtered ===", new_count, len(matched))


if __name__ == "__main__":
    main()
