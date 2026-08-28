# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from src.models import JobResult, RunResult

def make_run(run_id="2026-08-27-0800", track="generic-saas"):
    return RunResult(
        run_id=run_id, track=track, triggered_by="ui",
        started_at="2026-08-27T08:00:00", completed_at="2026-08-27T08:02:00",
        jobs=[JobResult(
            title="VP of Engineering", company="Acme", location="Remote, US",
            posted_date="2026-08-25", fit_score=82, gaps=[], url="https://example.com",
            track=track,
        )]
    )

@pytest.fixture
def client():
    # Patch start_scheduler so it doesn't actually start a background thread
    with patch("src.api.start_scheduler"):
        from src.api import app
        return TestClient(app)

def test_get_config_track(client):
    mock_config = {"name": "Generic SaaS VP/Director", "enabled": True, "titles": [], "keywords": {}}
    with patch("src.api.load_track", return_value=mock_config):
        resp = client.get("/api/config/generic-saas")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Generic SaaS VP/Director"

def test_post_config_track(client):
    with patch("src.api.save_track") as mock_save:
        resp = client.post("/api/config/generic-saas", json={"name": "test"})
        assert resp.status_code == 200
        mock_save.assert_called_once()

def test_get_config_shared(client):
    mock_criteria = {"location": {"remote": True, "country": "US"}, "posting": {"max_days": 14}}
    with patch("src.api.load_shared_criteria", return_value=mock_criteria):
        resp = client.get("/api/config/shared")
        assert resp.status_code == 200

def test_trigger_run(client):
    mock_run = make_run()
    with patch("src.api.run_job_search", new=AsyncMock(return_value=mock_run)):
        with patch("src.api.store.save_run", return_value="2026-08-27-0800"):
            resp = client.post("/api/run?track=generic-saas&source=ui")
            assert resp.status_code == 200
            data = resp.json()
            assert "run_id" in data

def test_get_results(client):
    mock_run = make_run()
    with patch("src.api.store.list_runs", return_value=[mock_run]):
        resp = client.get("/api/results")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

def test_get_results_by_run_id(client):
    mock_run = make_run()
    with patch("src.api.store.get_run", return_value=mock_run):
        resp = client.get("/api/results/2026-08-27-0800")
        assert resp.status_code == 200
        assert resp.json()["run_id"] == "2026-08-27-0800"

def test_get_schedule(client):
    mock_status = {"enabled": False, "hour": 8, "minute": 0,
                   "timezone": "America/New_York", "tracks": "all", "next_run": None}
    with patch("src.api.get_schedule_status", return_value=mock_status):
        resp = client.get("/api/schedule")
        assert resp.status_code == 200
        assert "enabled" in resp.json()

def test_get_run_status_no_runs(client):
    with patch("src.api.store.get_latest_run", return_value=None):
        resp = client.get("/api/run/status")
        assert resp.status_code == 200
        assert resp.json()["status"] == "no_runs"

def test_get_latest_logs_no_runs(client):
    with patch("src.api.store.get_latest_run", return_value=None):
        resp = client.get("/api/logs/latest")
        assert resp.status_code == 200
        assert resp.json()["events"] == []

def test_get_logs_by_run_id(client):
    with patch("src.api.logger.load", return_value={"events": ["[08:00:00] started"], "llm": [], "debug": []}):
        resp = client.get("/api/logs/2026-08-27-0800")
        assert resp.status_code == 200
        assert len(resp.json()["events"]) == 1
