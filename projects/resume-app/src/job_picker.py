# src/job_picker.py
"""
job_picker.py — Entry point for job search runs.
Orchestrates: scraper -> filter -> RunResult (with kept + skipped).
"""

import asyncio
from datetime import datetime, timezone
from typing import List

from src.config import load_shared_criteria, load_track, build_linkedin_query
from src.scraper import scrape_job_cards, fetch_descriptions
from src.job_filter import filter_jobs, _title_excluded
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


async def _search_one_track(track_name: str, criteria: dict, run_id: str = ""):
    """
    Two-phase search for a single track:
      1. Scrape all cards from LinkedIn (fast, one page load)
      2. Apply title filter — drop obvious mismatches before any description fetch
      3. Fetch descriptions only for title-passing jobs
      4. LLM filter + score
    """
    from src.models import SkippedJob
    from src.job_filter import FilterResult

    track_cfg = load_track(track_name)
    query = (
        track_cfg.get("search_query")
        or build_linkedin_query(track_cfg)
        or TRACK_QUERIES.get(track_name, track_name)
    )
    location = "United States" if criteria.get("location", {}).get("country") == "US" else "Worldwide"
    max_days = criteria.get("posting", {}).get("max_days", 1)
    domain_excludes = [kw.lower() for kw in track_cfg.get("keywords", {}).get("domain_exclude", [])]

    logger.log_event(f"Scraping track: {track_name} — last {max_days} days")
    logger.log_debug(f"LinkedIn query: {query}")

    # Phase 1 — scrape cards (one page, fast)
    cards = await scrape_job_cards(query, location, max_results=60, max_days=max_days, run_id=run_id)
    logger.log_event(f"Track {track_name}: {len(cards)} cards scraped from LinkedIn")

    # Phase 2 — title filter before any description fetch
    title_skipped: List[SkippedJob] = []
    passing: List[dict] = []
    for card in cards:
        kw = _title_excluded(card.get("title", ""), domain_excludes)
        if kw:
            title_skipped.append(SkippedJob(
                title=card["title"], company=card.get("company", ""),
                url=card.get("url", ""),
                reason=f'Title contains excluded domain: "{kw}"',
                track=track_name,
            ))
        else:
            passing.append(card)

    logger.log_event(
        f"Track {track_name}: {len(passing)} passed title filter, "
        f"{len(title_skipped)} dropped — fetching descriptions"
    )

    # Phase 3 — fetch descriptions only for passing jobs
    passing = await fetch_descriptions(passing, run_id=run_id)

    # Phase 4 — LLM filter + score
    result = await filter_jobs(passing, track_name)

    # Merge title-skipped with LLM-skipped
    combined = FilterResult(
        kept=result.kept,
        skipped=title_skipped + result.skipped,
    )
    logger.log_event(
        f"Track {track_name}: {len(combined.kept)} kept, "
        f"{len(combined.skipped)} total filtered"
    )
    return combined


async def run_job_search(
    track: str = "all",
    triggered_by: str = "ui",
) -> RunResult:
    """
    Run a job search for one or all tracks.
    Returns a RunResult with all matched jobs and skipped jobs.
    """
    run_id = _run_id()
    logger.clear()
    started_at = datetime.now(timezone.utc).isoformat()
    logger.log_event(f"Run started — track: {track}, triggered_by: {triggered_by}")

    criteria = load_shared_criteria()
    tracks_to_search = TRACKS if track == "all" else [track]

    all_kept: List[JobResult] = []
    all_skipped: List[SkippedJob] = []

    for track_name in tracks_to_search:
        result = await _search_one_track(track_name, criteria, run_id=run_id)
        all_kept.extend(result.kept)
        all_skipped.extend(result.skipped)

    completed_at = datetime.now(timezone.utc).isoformat()
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
