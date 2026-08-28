# src/store.py
"""
store.py — File-based persistence for RunResult objects.
Each run is saved as a JSON file: <STORE_DIR>/<run_id>.json
DB-swap ready: to switch to a database, replace only this file.
STORE_DIR env var overrides the default path (used in tests).
"""

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional

from src.models import JobResult, RunResult, SkippedJob, TrackedJob


def _store_dir() -> Path:
    """Return the storage directory. Overrideable via STORE_DIR env var."""
    override = os.environ.get("STORE_DIR")
    if override:
        return Path(override)
    return Path(__file__).parent.parent / "data" / "runs"


def _run_path(run_id: str) -> Path:
    return _store_dir() / f"{run_id}.json"


def _run_from_dict(data: dict) -> RunResult:
    """Deserialize a dict into a RunResult (with nested JobResult + SkippedJob lists)."""
    from src.models import JobResult, RunResult, SkippedJob, TrackedJob
    jobs = [JobResult(**j) for j in data.pop("jobs", [])]
    skipped = [SkippedJob(**s) for s in data.pop("skipped", [])]
    return RunResult(**data, jobs=jobs, skipped=skipped)


def save_run(run: RunResult) -> str:
    """
    Persist a RunResult to disk as JSON.
    Returns the run_id.
    """
    store_dir = _store_dir()
    store_dir.mkdir(parents=True, exist_ok=True)
    path = _run_path(run.run_id)
    with open(path, "w") as f:
        json.dump(asdict(run), f, indent=2)
    return run.run_id


def get_run(run_id: str) -> RunResult:
    """
    Load a RunResult by run_id.
    Raises FileNotFoundError if not found.
    """
    path = _run_path(run_id)
    if not path.exists():
        raise FileNotFoundError(f"Run not found: {run_id}")
    with open(path, "r") as f:
        data = json.load(f)
    return _run_from_dict(data)


def list_runs(track: Optional[str] = None, limit: int = 20) -> List[RunResult]:
    """
    List saved runs, sorted newest-first by run_id (lexicographic = chronological).
    Optionally filter by track. Returns at most `limit` results.
    """
    store_dir = _store_dir()
    if not store_dir.exists():
        return []

    paths = sorted(store_dir.glob("*.json"), reverse=True)
    results = []
    for path in paths:
        if len(results) >= limit:
            break
        try:
            with open(path, "r") as f:
                data = json.load(f)
            run = _run_from_dict(data)
            if track and run.track != track:
                continue
            results.append(run)
        except Exception:
            continue  # skip corrupt files
    return results


def get_latest_run() -> Optional[RunResult]:
    """Return the most recently saved run, or None if no runs exist."""
    runs = list_runs(limit=1)
    return runs[0] if runs else None


# ── Tracking ──────────────────────────────────────────────────────────────────

def _tracking_path() -> Path:
    p = _store_dir().parent / "tracked_jobs.json"
    return p


def _load_tracking_raw() -> List[dict]:
    path = _tracking_path()
    if not path.exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save_tracking_raw(jobs: List[dict]) -> None:
    path = _tracking_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(jobs, f, indent=2)


def get_tracked_jobs() -> List[TrackedJob]:
    """Return all tracked jobs, newest-added first."""
    raw = _load_tracking_raw()
    jobs = [TrackedJob(**j) for j in raw]
    return sorted(jobs, key=lambda j: j.added_at, reverse=True)


def add_tracked_job(job: TrackedJob) -> None:
    """Add a job to tracking. Idempotent — updates if URL already exists."""
    raw = _load_tracking_raw()
    raw = [j for j in raw if j["url"] != job.url]  # remove old entry if exists
    raw.append(asdict(job))
    _save_tracking_raw(raw)


def update_tracked_job(url: str, status: str = None, notes: str = None) -> bool:
    """Update status and/or notes for a tracked job. Returns False if not found."""
    raw = _load_tracking_raw()
    for job in raw:
        if job["url"] == url:
            if status is not None:
                job["status"] = status
            if notes is not None:
                job["notes"] = notes
            _save_tracking_raw(raw)
            return True
    return False


def remove_tracked_job(url: str) -> bool:
    """Remove a job from tracking. Returns False if not found."""
    raw = _load_tracking_raw()
    new_raw = [j for j in raw if j["url"] != url]
    if len(new_raw) == len(raw):
        return False
    _save_tracking_raw(new_raw)
    return True
