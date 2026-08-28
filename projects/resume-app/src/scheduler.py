# src/scheduler.py
"""
scheduler.py — APScheduler integration for daily job searches.
Schedule is persisted to config/schedule.yaml so it survives restarts.
"""

import asyncio
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from src.config import load_schedule, save_schedule

scheduler = BackgroundScheduler()


def _run_job_search_sync(tracks: str = "all") -> None:
    """Sync wrapper for the async job search — called by APScheduler."""
    from src.job_picker import run_job_search
    from src import store
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(
            run_job_search(track=tracks, triggered_by="schedule")
        )
        store.save_run(result)
    finally:
        loop.close()


def start_scheduler() -> None:
    """Start the scheduler and restore saved schedule from config."""
    if not scheduler.running:
        scheduler.start()
    try:
        config = load_schedule()
        if config.get("enabled"):
            set_schedule(
                hour=config["hour"],
                minute=config["minute"],
                enabled=True,
                tracks=config.get("tracks", "all"),
            )
    except Exception:
        pass


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)


def set_schedule(
    hour: int,
    minute: int,
    enabled: bool,
    tracks: str = "all",
) -> None:
    """Set or clear the daily job search schedule."""
    scheduler.remove_all_jobs()
    if enabled:
        scheduler.add_job(
            _run_job_search_sync,
            trigger=CronTrigger(hour=hour, minute=minute, timezone="America/New_York"),
            kwargs={"tracks": tracks},
            id="daily_job_search",
            replace_existing=True,
        )
    save_schedule({
        "enabled": enabled,
        "hour": hour,
        "minute": minute,
        "timezone": "America/New_York",
        "tracks": tracks,
    })


def get_schedule_status() -> dict:
    """Return current schedule config and next run time."""
    config = load_schedule()
    next_run: Optional[str] = None
    job = scheduler.get_job("daily_job_search")
    if job and job.next_run_time:
        next_run = job.next_run_time.isoformat()
    return {
        "enabled": config.get("enabled", False),
        "hour": config.get("hour", 8),
        "minute": config.get("minute", 0),
        "timezone": config.get("timezone", "America/New_York"),
        "tracks": config.get("tracks", "all"),
        "next_run": next_run,
    }
