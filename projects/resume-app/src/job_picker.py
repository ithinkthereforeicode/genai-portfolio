# src/job_picker.py
"""
job_picker.py — Entry point for job search runs.
Orchestrates: scraper -> filter -> RunResult (with kept + skipped).
"""

import asyncio
from datetime import datetime, timezone
from typing import List

from src.config import load_shared_criteria, load_track
from src.scraper import search_linkedin
from src.job_filter import filter_jobs
from src.models import JobResult, SkippedJob, RunResult
from src.logger import logger

TRACKS = ["generic-saas", "data-ai", "identity-security"]

# Fallback queries if track YAML has no search_query field
TRACK_QUERIES = {
    "generic-saas": "VP of Engineering OR Director of Engineering",
    "data-ai": "VP of Data AI OR Director of Machine Learning",
    "identity-security": "VP of Identity OR Director of Security Engineering",
}


def _run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")


async def _search_one_track(track_name: str, criteria: dict):
    """Search and filter jobs for a single track. Returns FilterResult."""
    # Prefer search_query from track YAML, fall back to hardcoded default
    track_cfg = load_track(track_name)
    query = track_cfg.get("search_query") or TRACK_QUERIES.get(track_name, track_name)

    location = "United States" if criteria.get("location", {}).get("country") == "US" else "Worldwide"
    max_days = criteria.get("posting", {}).get("max_days", 7)

    logger.log_event(f"Scraping track: {track_name} — last {max_days} days")
    logger.log_debug(f"LinkedIn query: {query}")
    raw_jobs = await search_linkedin(query, location, max_results=25, max_days=max_days)
    logger.log_event(f"Track {track_name}: {len(raw_jobs)} raw jobs found, filtering...")

    result = await filter_jobs(raw_jobs, track_name)
    logger.log_event(f"Track {track_name}: {len(result.kept)} kept, {len(result.skipped)} filtered out")
    return result


async def run_job_search(
    track: str = "all",
    triggered_by: str = "ui",
) -> RunResult:
    """
    Run a job search for one or all tracks.
    Returns a RunResult with all matched jobs and skipped jobs.
    """
    logger.clear()
    started_at = datetime.now(timezone.utc).isoformat()
    logger.log_event(f"Run started — track: {track}, triggered_by: {triggered_by}")

    criteria = load_shared_criteria()
    tracks_to_search = TRACKS if track == "all" else [track]

    all_kept: List[JobResult] = []
    all_skipped: List[SkippedJob] = []

    for track_name in tracks_to_search:
        result = await _search_one_track(track_name, criteria)
        all_kept.extend(result.kept)
        all_skipped.extend(result.skipped)

    completed_at = datetime.now(timezone.utc).isoformat()
    run_id = _run_id()
    logger.log_event(f"Run complete — {len(all_kept)} jobs kept, {len(all_skipped)} filtered. run_id: {run_id}")
    logger.save(run_id)

    return RunResult(
        run_id=run_id,
        track=track,
        triggered_by=triggered_by,
        started_at=started_at,
        completed_at=completed_at,
        jobs=all_kept,
        skipped=all_skipped,
    )
