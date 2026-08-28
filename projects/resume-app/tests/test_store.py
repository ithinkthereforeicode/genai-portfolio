# tests/test_store.py
import pytest
import json
from pathlib import Path
from src.models import JobResult, RunResult

def make_run(run_id="2026-08-26-0800", track="generic-saas"):
    return RunResult(
        run_id=run_id,
        track=track,
        triggered_by="ui",
        started_at="2026-08-26T08:00:00",
        completed_at="2026-08-26T08:02:00",
        jobs=[
            JobResult(
                title="VP of Engineering",
                company="Acme Corp",
                location="Remote, US",
                posted_date="2026-08-25",
                fit_score=82,
                gaps=["Kubernetes experience"],
                url="https://linkedin.com/jobs/123",
                track=track,
            )
        ],
    )

def test_save_and_get_run(tmp_path, monkeypatch):
    """save_run writes a run; get_run reads it back."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    run = make_run()
    run_id = store.save_run(run)
    assert run_id == "2026-08-26-0800"
    loaded = store.get_run(run_id)
    assert loaded.run_id == run_id
    assert loaded.track == "generic-saas"
    assert len(loaded.jobs) == 1
    assert loaded.jobs[0].title == "VP of Engineering"

def test_list_runs_returns_all(tmp_path, monkeypatch):
    """list_runs returns all saved runs sorted newest-first."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    store.save_run(make_run("2026-08-25-0800"))
    store.save_run(make_run("2026-08-26-0800"))
    runs = store.list_runs()
    assert len(runs) == 2
    # Newest first
    assert runs[0].run_id == "2026-08-26-0800"

def test_list_runs_filter_by_track(tmp_path, monkeypatch):
    """list_runs with track= filters to that track only."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    store.save_run(make_run("2026-08-25-0800", track="generic-saas"))
    store.save_run(make_run("2026-08-26-0800", track="data-ai"))
    runs = store.list_runs(track="data-ai")
    assert len(runs) == 1
    assert runs[0].track == "data-ai"

def test_get_latest_run(tmp_path, monkeypatch):
    """get_latest_run returns the most recently saved run."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    store.save_run(make_run("2026-08-25-0800"))
    store.save_run(make_run("2026-08-26-0800"))
    latest = store.get_latest_run()
    assert latest.run_id == "2026-08-26-0800"

def test_get_run_missing_raises(tmp_path, monkeypatch):
    """get_run raises FileNotFoundError for unknown run_id."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        store.get_run("nonexistent-id")

def test_get_latest_run_empty(tmp_path, monkeypatch):
    """get_latest_run returns None when no runs exist."""
    from src import store
    monkeypatch.setenv("STORE_DIR", str(tmp_path))
    assert store.get_latest_run() is None
