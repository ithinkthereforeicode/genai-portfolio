# src/api_client.py
"""
api_client.py — HTTP client for the FastAPI backend.
Used by app.py (Streamlit). Never imports src modules directly.
API_URL defaults to http://localhost:8000, overrideable via env var.
"""

import os
from typing import Optional
import requests

API_URL = os.environ.get("API_URL", "http://localhost:8000")


def _get(path: str, params: dict = None) -> dict:
    resp = requests.get(f"{API_URL}{path}", params=params or {})
    resp.raise_for_status()
    return resp.json()


def _post(path: str, data: dict = None, params: dict = None):
    resp = requests.post(f"{API_URL}{path}", json=data or {}, params=params or {})
    resp.raise_for_status()
    return resp.json()


def get_track_config(track: str) -> dict:
    return _get(f"/api/config/{track}")


def save_track_config(track: str, data: dict) -> bool:
    try:
        _post(f"/api/config/{track}", data)
        return True
    except requests.HTTPError:
        return False


def get_shared_config() -> dict:
    return _get("/api/config/shared")


def save_shared_config(data: dict) -> bool:
    try:
        _post("/api/config/shared", data)
        return True
    except requests.HTTPError:
        return False


def trigger_run(track: str = "all", source: str = "ui") -> dict:
    return _post("/api/run", params={"track": track, "source": source})


def get_run_status() -> dict:
    try:
        return _get("/api/run/status")
    except Exception:
        return {"status": "unknown"}


def get_schedule() -> dict:
    return _get("/api/schedule")


def save_schedule(data: dict) -> bool:
    try:
        _post("/api/schedule", data)
        return True
    except requests.HTTPError:
        return False


def get_results(track: Optional[str] = None, limit: int = 20) -> list:
    params = {"limit": limit}
    if track:
        params["track"] = track
    return _get("/api/results", params=params)


def get_result(run_id: str) -> dict:
    return _get(f"/api/results/{run_id}")


def get_logs(run_id: str = "latest") -> dict:
    """Fetch logs for a run_id, or 'latest' for the most recent run."""
    return _get(f"/api/logs/{run_id}")


def get_llm_config() -> dict:
    """Fetch LLM provider config."""
    return _get("/api/config/llm")


def save_llm_config(data: dict) -> bool:
    """Save LLM provider config."""
    try:
        _post("/api/config/llm", data)
        return True
    except requests.HTTPError:
        return False
