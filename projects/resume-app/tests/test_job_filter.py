# tests/test_job_filter.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_should_skip_citizenship_required():
    """Jobs requiring US citizenship should be skipped."""
    from src.job_filter import should_skip_job
    jd = "Must be a US citizen or have active security clearance required."
    track = {"keywords": {"required": ["software"], "preferred": [], "domain_exclude": []}}
    keywords = {
        "exclude": [],
        "citizenship_exclude": ["US citizen required", "security clearance required"],
        "domain_experience_rule": "Skip if 3+ years domain required",
    }
    with patch("src.job_filter._llm_judge", new=AsyncMock(return_value='{"skip": true, "reason": "Requires US citizenship"}')):
        skip, reason = await should_skip_job(jd, track, keywords)
        assert skip is True

@pytest.mark.asyncio
async def test_filter_jobs_returns_filter_result():
    """filter_jobs returns a FilterResult with kept and skipped."""
    from src.job_filter import filter_jobs, FilterResult
    from src.models import JobResult
    raw_jobs = [
        {
            "title": "VP of Engineering",
            "company": "Acme",
            "location": "Remote",
            "posted_date": "2026-08-25",
            "url": "https://example.com",
            "description": "Looking for VP of Engineering for SaaS company.",
        }
    ]
    with patch("src.job_filter.should_skip_job", new=AsyncMock(return_value=(False, ""))):
        with patch("src.job_filter._score_job", new=AsyncMock(return_value=75)):
            with patch("src.job_filter.load_track", return_value={"keywords": {"preferred": ["SaaS"], "domain_exclude": []}}):
                with patch("src.job_filter.load_keywords", return_value={"citizenship_exclude": [], "domain_experience_rule": ""}):
                    result = await filter_jobs(raw_jobs, "generic-saas")
                    assert isinstance(result, FilterResult)
                    assert len(result.kept) == 1
                    assert isinstance(result.kept[0], JobResult)
                    assert result.skipped == []

@pytest.mark.asyncio
async def test_filter_jobs_excludes_skipped():
    """Jobs flagged by should_skip_job go to skipped list with reason."""
    from src.job_filter import filter_jobs
    from src.models import SkippedJob
    raw_jobs = [
        {
            "title": "VP of Engineering",
            "company": "Acme",
            "location": "Remote",
            "posted_date": "2026-08-25",
            "url": "https://example.com",
            "description": "Must be US citizen.",
        }
    ]
    with patch("src.job_filter.should_skip_job", new=AsyncMock(return_value=(True, "Citizenship required"))):
        with patch("src.job_filter.load_track", return_value={"keywords": {"preferred": [], "domain_exclude": []}}):
            with patch("src.job_filter.load_keywords", return_value={"citizenship_exclude": [], "domain_experience_rule": ""}):
                result = await filter_jobs(raw_jobs, "generic-saas")
                assert result.kept == []
                assert len(result.skipped) == 1
                assert isinstance(result.skipped[0], SkippedJob)
                assert result.skipped[0].reason == "Citizenship required"

@pytest.mark.asyncio
async def test_filter_jobs_sorts_by_score():
    """filter_jobs returns kept jobs sorted by fit_score descending."""
    from src.job_filter import filter_jobs
    raw_jobs = [
        {"title": "Job A", "company": "Co", "location": "Remote", "posted_date": "2026-08-25", "url": "https://a.com", "description": "A"},
        {"title": "Job B", "company": "Co", "location": "Remote", "posted_date": "2026-08-25", "url": "https://b.com", "description": "B"},
    ]
    score_mock = AsyncMock(side_effect=[30, 80])
    with patch("src.job_filter.should_skip_job", new=AsyncMock(return_value=(False, ""))):
        with patch("src.job_filter._score_job", new=score_mock):
            with patch("src.job_filter.load_track", return_value={"keywords": {"preferred": [], "domain_exclude": []}}):
                with patch("src.job_filter.load_keywords", return_value={"citizenship_exclude": [], "domain_experience_rule": ""}):
                    result = await filter_jobs(raw_jobs, "generic-saas")
                    kept = result.kept
                    assert len(kept) == 2
                    assert kept[0].fit_score >= kept[1].fit_score
                    assert kept[0].title == "Job B"
