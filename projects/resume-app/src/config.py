# src/config.py
"""
config.py — YAML I/O wrapper.
All config reads/writes go through here; nothing else reads YAML directly.
CONFIG_DIR env var overrides the default path (used in tests).
"""

import os
from pathlib import Path
from typing import Dict
import yaml

def _config_dir() -> Path:
    """Return the config directory. Overrideable via CONFIG_DIR env var."""
    override = os.environ.get("CONFIG_DIR")
    if override:
        return Path(override)
    # Default: config/ relative to project root (two levels up from src/)
    return Path(__file__).parent.parent / "config"


def load_track(track_name: str) -> dict:
    """Load a track YAML file by name (e.g. 'generic-saas')."""
    path = _config_dir() / "tracks" / f"{track_name}.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_track(track_name: str, data: dict) -> None:
    """Write a track config dict back to YAML."""
    path = _config_dir() / "tracks" / f"{track_name}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def load_all_tracks() -> Dict[str, dict]:
    """Load all track YAML files. Returns dict keyed by track slug."""
    tracks_dir = _config_dir() / "tracks"
    result = {}
    for path in sorted(tracks_dir.glob("*.yaml")):
        key = path.stem  # filename without extension
        with open(path, "r") as f:
            result[key] = yaml.safe_load(f) or {}
    return result


def load_shared_criteria() -> dict:
    """Load job_criteria.yaml (shared filters: location, posting age, company size)."""
    path = _config_dir() / "job_criteria.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_shared_criteria(data: dict) -> None:
    """Write shared criteria back to job_criteria.yaml."""
    path = _config_dir() / "job_criteria.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def load_keywords() -> dict:
    """Load keywords.yaml."""
    path = _config_dir() / "keywords.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_keywords(data: dict) -> None:
    """Write keywords.yaml."""
    path = _config_dir() / "keywords.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def load_schedule() -> dict:
    """Load schedule.yaml."""
    path = _config_dir() / "schedule.yaml"
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_schedule(data: dict) -> None:
    """Write schedule.yaml."""
    path = _config_dir() / "schedule.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)


def load_llm_config() -> dict:
    """Load LLM provider config from config/llm.yaml."""
    path = _config_dir() / "llm.yaml"
    if not path.exists():
        return {
            "provider": "lmstudio",
            "model": "google/gemma-4-12b-qat",
            "max_tokens": 300,
            "temperature": 0.1,
        }
    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_llm_config(data: dict) -> None:
    """Write LLM config back to llm.yaml."""
    path = _config_dir() / "llm.yaml"
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
