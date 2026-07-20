"""
Tests for the job aggregator.

NEW SKILL: automated testing. These don't hit the real API (tests
should never depend on live external services -- they'd be slow and
flaky). Instead we test the logic against fake, controlled data.
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import aggregator  # noqa: E402


FAKE_JOBS = [
    {"id": "1", "position": "Senior Python Developer", "company": "Acme",
     "description": "We need a Python backend engineer", "tags": ["python", "backend"],
     "url": "https://example.com/1"},
    {"id": "2", "position": "Frontend React Developer", "company": "Beta",
     "description": "React and TypeScript role", "tags": ["react", "frontend"],
     "url": "https://example.com/2"},
    {"id": "3", "position": "Data Engineer", "company": "Gamma",
     "description": "Python and SQL pipelines", "tags": ["python", "sql"],
     "url": "https://example.com/3"},
]


def test_filter_jobs_matches_keyword():
    result = aggregator.filter_jobs(FAKE_JOBS, ["python"])
    ids = {job["id"] for job in result}
    assert ids == {"1", "3"}


def test_filter_jobs_no_match_returns_empty():
    result = aggregator.filter_jobs(FAKE_JOBS, ["rust"])
    assert result == []


def test_filter_jobs_multiple_keywords():
    result = aggregator.filter_jobs(FAKE_JOBS, ["react", "sql"])
    ids = {job["id"] for job in result}
    assert ids == {"2", "3"}


def test_db_dedup_flow():
    # use a temp db so tests don't touch real data
    with tempfile.TemporaryDirectory() as tmp:
        aggregator.DB_PATH = os.path.join(tmp, "test_jobs.db")
        aggregator.init_db()

        job = FAKE_JOBS[0]
        assert aggregator.is_new_job(job["id"]) is True

        aggregator.save_job(job)
        assert aggregator.is_new_job(job["id"]) is False
