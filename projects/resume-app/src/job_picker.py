# src/job_picker.py
"""
job_picker.py — Entry point for job search runs.
Orchestrates: scraper -> filter -> RunResult.
"""

import asyncio
from datetime import datetime, timezone
from typing import List

from src.config import load_shared_criteria
from src.scraper import search_linkedin
from src.job_filter import filter_jobs
from src.models import JobResult, RunResult

TRACKS = ["generic-saas", "data-ai", "identity-security"]

TRACK_QUERIES = {
    "generic-saas": "VP of Engineering OR Director of Engineering",
    "data-ai": "VP of Data AI OR Director of Machine Learning",
    "identity-security": "VP of Identity OR Director of Security Engineering",
}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")


async def _search_one_track(track_name: str, criteria: dict) -> List[JobResult]:
    """Search and filter jobs for a single track."""
    query = TRACK_QUERIES.get(track_name, track_name)
    location = "United States" if criteria.get("location", {}).get("country") == "US" else "Worldwide"
    max_results = 25

    raw_jobs = await search_linkedin(query, location, max_results=max_results)
    return await filter_jobs(raw_jobs, track_name)


async def run_job_search(
    track: str = "all",
    triggered_by: str = "ui",
) -> RunResult:
    """
    Run a job search for one or all tracks.
    Returns a RunResult with all matched jobs.
    """
    started_at = datetime.now(timezone.utc).isoformat()
    criteria = load_shared_criteria()

    tracks_to_search = TRACKS if track == "all" else [track]

    all_jobs: List[JobResult] = []
    for track_name in tracks_to_search:
        jobs = await _search_one_track(track_name, criteria)
        all_jobs.extend(jobs)

    completed_at = datetime.now(timezone.utc).isoformat()

    return RunResult(
        run_id=_run_id(),
        track=track,
        triggered_by=triggered_by,
        started_at=started_at,
        completed_at=completed_at,
        jobs=all_jobs,
    )
