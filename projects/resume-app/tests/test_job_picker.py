# tests/test_job_picker.py
import pytest
from unittest.mock import AsyncMock, patch
from src.models import JobResult, RunResult

def make_job(track="generic-saas"):
    return JobResult(
        title="VP of Engineering", company="Acme", location="Remote, US",
        posted_date="2026-08-25", fit_score=82, gaps=[], url="https://example.com",
        track=track,
    )

@pytest.mark.asyncio
async def test_run_job_search_returns_run_result():
    from src.job_picker import run_job_search
    with patch("src.job_picker.search_linkedin", new=AsyncMock(return_value=[])):
        with patch("src.job_picker.filter_jobs", new=AsyncMock(return_value=[make_job()])):
            with patch("src.job_picker.load_shared_criteria", return_value={"location": {"remote": True, "country": "US"}}):
                result = await run_job_search(track="generic-saas", triggered_by="ui")
                assert isinstance(result, RunResult)
                assert result.track == "generic-saas"
                assert result.triggered_by == "ui"
                assert len(result.jobs) == 1

@pytest.mark.asyncio
async def test_run_job_search_all_tracks():
    from src.job_picker import run_job_search
    with patch("src.job_picker.search_linkedin", new=AsyncMock(return_value=[])):
        with patch("src.job_picker.filter_jobs", new=AsyncMock(return_value=[make_job()])):
            with patch("src.job_picker.load_shared_criteria", return_value={"location": {"remote": True, "country": "US"}}):
                result = await run_job_search(track="all", triggered_by="schedule")
                assert isinstance(result, RunResult)
                assert result.track == "all"
                assert result.triggered_by == "schedule"
                # all = 3 tracks, each returns 1 job
                assert len(result.jobs) == 3

@pytest.mark.asyncio
async def test_run_job_search_sets_timestamps():
    from src.job_picker import run_job_search
    with patch("src.job_picker.search_linkedin", new=AsyncMock(return_value=[])):
        with patch("src.job_picker.filter_jobs", new=AsyncMock(return_value=[])):
            with patch("src.job_picker.load_shared_criteria", return_value={"location": {"remote": True, "country": "US"}}):
                result = await run_job_search(track="all")
                assert result.started_at != ""
                assert result.completed_at != ""
                assert result.run_id != ""
