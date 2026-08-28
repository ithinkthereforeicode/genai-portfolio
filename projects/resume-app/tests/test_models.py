from src.models import JobResult, RunResult

def test_job_result_fields():
    job = JobResult(
        title="VP of Engineering",
        company="Acme Corp",
        location="Remote, US",
        posted_date="2026-08-25",
        fit_score=82,
        gaps=["MLOps", "team size >50"],
        url="https://linkedin.com/jobs/123",
        track="generic-saas",
    )
    assert job.title == "VP of Engineering"
    assert job.fit_score == 82
    assert "MLOps" in job.gaps

def test_run_result_fields():
    job = JobResult(
        title="VP of Engineering", company="Acme", location="Remote, US",
        posted_date="2026-08-25", fit_score=82, gaps=[], url="https://example.com",
        track="generic-saas",
    )
    run = RunResult(
        run_id="2026-08-27-0800",
        track="generic-saas",
        triggered_by="ui",
        started_at="2026-08-27T08:00:00",
        completed_at="2026-08-27T08:02:00",
        jobs=[job],
    )
    assert run.run_id == "2026-08-27-0800"
    assert len(run.jobs) == 1
    assert run.triggered_by == "ui"
