# tests/test_api_client.py
from unittest.mock import patch, MagicMock
import requests

def make_mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock

def test_get_track_config():
    from src.api_client import get_track_config
    mock_data = {"name": "Generic SaaS", "titles": [], "keywords": {}}
    with patch("requests.get", return_value=make_mock_response(mock_data)):
        result = get_track_config("generic-saas")
        assert result["name"] == "Generic SaaS"

def test_save_track_config_returns_true_on_success():
    from src.api_client import save_track_config
    with patch("requests.post", return_value=make_mock_response({"status": "saved"})):
        result = save_track_config("generic-saas", {"name": "test"})
        assert result is True

def test_save_track_config_returns_false_on_error():
    from src.api_client import save_track_config
    mock_resp = make_mock_response({}, status_code=500)
    mock_resp.raise_for_status.side_effect = requests.HTTPError()
    with patch("requests.post", return_value=mock_resp):
        result = save_track_config("generic-saas", {})
        assert result is False

def test_trigger_run():
    from src.api_client import trigger_run
    mock_data = {"run_id": "2026-08-27-0800", "status": "completed", "jobs_found": 5}
    with patch("requests.post", return_value=make_mock_response(mock_data)):
        result = trigger_run(track="all", source="ui")
        assert result["run_id"] == "2026-08-27-0800"

def test_get_results():
    from src.api_client import get_results
    mock_data = [{"run_id": "2026-08-27-0800", "track": "generic-saas", "jobs": []}]
    with patch("requests.get", return_value=make_mock_response(mock_data)):
        result = get_results()
        assert isinstance(result, list)
        assert result[0]["run_id"] == "2026-08-27-0800"

def test_get_schedule():
    from src.api_client import get_schedule
    mock_data = {"enabled": False, "hour": 8, "minute": 0, "tracks": "all", "next_run": None}
    with patch("requests.get", return_value=make_mock_response(mock_data)):
        result = get_schedule()
        assert "enabled" in result

def test_save_schedule_returns_true():
    from src.api_client import save_schedule
    with patch("requests.post", return_value=make_mock_response({"status": "saved"})):
        result = save_schedule({"enabled": True, "hour": 8, "minute": 0})
        assert result is True
