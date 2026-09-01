# tests/test_job_picker.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.models import JobResult, RunResult, SkippedJob
from src.job_filter import FilterResult


def make_job(track="generic-saas"):
    return JobResult(
        title="VP of Engineering", company="Acme", location="Remote, US",
        posted_date="2026-08-25", fit_score=82, gaps=[], url="https://example.com",
        track=track,
    )


def make_filter_result(track="generic-saas"):
    return FilterResult(kept=[make_job(track)], skipped=[])


# Shared patch helpers — mock the two-phase scraper functions and filter
def _base_patches(filter_result):
    """Return context managers that mock scraping + filtering for job_picker tests."""
    return [
        patch("src.job_picker.scrape_job_cards", new=AsyncMock(return_value=[])),
        patch("src.job_picker.fetch_descriptions", new=AsyncMock(side_effect=lambda jobs, **kw: jobs)),
        patch("src.job_picker._title_excluded", return_value=None),
        patch("src.job_picker.filter_jobs", new=AsyncMock(return_value=filter_result)),
        patch("src.job_picker.load_shared_criteria",
              return_value={"location": {"remote": True, "country": "US"}, "posting": {"max_days": 1}}),
        patch("src.job_picker.load_track", return_value={"keywords": {"domain_exclude": []}}),
        patch("src.job_picker.build_linkedin_query", return_value="VP Engineering"),
    ]


@pytest.mark.asyncio
async def test_run_job_search_returns_run_result():
    from src.job_picker import run_job_search
    patches = _base_patches(make_filter_result())
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = await run_job_search(track="generic-saas", triggered_by="ui")
        assert isinstance(result, RunResult)
        assert result.track == "generic-saas"
        assert result.triggered_by == "ui"
        assert len(result.jobs) == 1
        assert result.skipped == []


@pytest.mark.asyncio
async def test_run_job_search_all_tracks():
    from src.job_picker import run_job_search, TRACKS
    patches = _base_patches(make_filter_result())
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = await run_job_search(track="all", triggered_by="schedule")
        assert isinstance(result, RunResult)
        assert result.track == "all"
        assert len(result.jobs) == len(TRACKS)  # one job per track


@pytest.mark.asyncio
async def test_run_job_search_sets_timestamps():
    from src.job_picker import run_job_search
    patches = _base_patches(FilterResult(kept=[], skipped=[]))
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = await run_job_search(track="all")
        assert result.started_at != ""
        assert result.completed_at != ""
        assert result.run_id != ""


@pytest.mark.asyncio
async def test_run_job_search_collects_skipped():
    from src.job_picker import run_job_search
    skipped = SkippedJob(title="Gov Job", company="GovCo", url="https://gov.com",
                         reason="US citizenship required", track="generic-saas")
    fr = FilterResult(kept=[], skipped=[skipped])
    patches = _base_patches(fr)
    with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6]:
        result = await run_job_search(track="generic-saas")
        assert len(result.skipped) == 1
        assert result.skipped[0].reason == "US citizenship required"
