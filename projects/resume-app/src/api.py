# src/api.py
"""
api.py — FastAPI backend.
Thin routes — no business logic in handlers.
All config I/O via src/config.py, all result I/O via src/store.py.
"""

from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src import store
from src.config import (
    load_track, save_track,
    load_shared_criteria, save_shared_criteria,
    load_keywords, save_keywords,
)
from src.scheduler import set_schedule, get_schedule_status, start_scheduler
from src.job_picker import run_job_search

app = FastAPI(title="Resume App API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    start_scheduler()


# ── Config ────────────────────────────────────────────────────────────────────

@app.get("/api/config/shared")
def get_shared_config():
    return load_shared_criteria()


@app.post("/api/config/shared")
def post_shared_config(data: dict):
    save_shared_criteria(data)
    return {"status": "saved"}


@app.get("/api/config/{track}")
def get_track_config(track: str):
    try:
        return load_track(track)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Track not found: {track}")


@app.post("/api/config/{track}")
def post_track_config(track: str, data: dict):
    save_track(track, data)
    return {"status": "saved"}


# ── Runs ──────────────────────────────────────────────────────────────────────

@app.post("/api/run")
async def trigger_run(track: str = "all", source: str = "ui"):
    result = await run_job_search(track=track, triggered_by=source)
    run_id = store.save_run(result)
    return {"run_id": run_id, "status": "completed", "jobs_found": len(result.jobs)}


@app.get("/api/run/status")
def run_status():
    latest = store.get_latest_run()
    if not latest:
        return {"status": "no_runs"}
    return {
        "run_id": latest.run_id,
        "track": latest.track,
        "triggered_by": latest.triggered_by,
        "completed_at": latest.completed_at,
        "jobs_found": len(latest.jobs),
    }


# ── Schedule ──────────────────────────────────────────────────────────────────

@app.get("/api/schedule")
def get_schedule():
    return get_schedule_status()


@app.post("/api/schedule")
def post_schedule(data: dict):
    set_schedule(
        hour=data.get("hour", 8),
        minute=data.get("minute", 0),
        enabled=data.get("enabled", False),
        tracks=data.get("tracks", "all"),
    )
    return {"status": "saved"}


# ── Results ───────────────────────────────────────────────────────────────────

@app.get("/api/results")
def get_results(track: Optional[str] = None, limit: int = 20):
    runs = store.list_runs(track=track, limit=limit)
    return [asdict(r) for r in runs]


@app.get("/api/results/{run_id}")
def get_result(run_id: str):
    try:
        run = store.get_run(run_id)
        return asdict(run)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
