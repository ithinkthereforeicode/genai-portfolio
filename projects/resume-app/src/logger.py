# src/logger.py
"""
logger.py — RunLogger singleton for 3-stream observability.
Streams: events (milestones), llm (per-job decisions), debug (verbose).
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict


def _log_dir() -> Path:
    override = os.environ.get("LOG_DIR")
    if override:
        return Path(override)
    return Path(__file__).parent.parent / "data" / "logs"


def _ts() -> str:
    return datetime.now().strftime("[%H:%M:%S]")


class RunLogger:
    def __init__(self):
        self._events: List[str] = []
        self._llm: List[str] = []
        self._debug: List[str] = []

    def log_event(self, msg: str) -> None:
        self._events.append(f"{_ts()} {msg}")

    def log_llm(self, msg: str) -> None:
        self._llm.append(f"{_ts()} {msg}")

    def log_debug(self, msg: str) -> None:
        self._debug.append(f"{_ts()} {msg}")

    def clear(self) -> None:
        self._events.clear()
        self._llm.clear()
        self._debug.clear()

    def get_all(self) -> Dict[str, List[str]]:
        return {
            "events": list(self._events),
            "llm": list(self._llm),
            "debug": list(self._debug),
        }

    def save(self, run_id: str) -> None:
        log_dir = _log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        path = log_dir / f"{run_id}.json"
        with open(path, "w") as f:
            json.dump(self.get_all(), f, indent=2)

    def load(self, run_id: str) -> Dict[str, List[str]]:
        path = _log_dir() / f"{run_id}.json"
        if not path.exists():
            return {"events": [], "llm": [], "debug": []}
        with open(path, "r") as f:
            return json.load(f)


# Module-level singleton
logger = RunLogger()
