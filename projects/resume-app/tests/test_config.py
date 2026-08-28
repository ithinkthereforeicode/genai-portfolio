# tests/test_config.py
import pytest
import yaml
from pathlib import Path

def test_load_track_returns_dict(tmp_path, monkeypatch):
    """load_track reads a track YAML and returns a dict."""
    from src.config import load_track
    track_dir = tmp_path / "tracks"
    track_dir.mkdir()
    track_file = track_dir / "generic-saas.yaml"
    track_file.write_text(yaml.dump({"name": "Generic SaaS", "titles": ["VP of Engineering"]}))
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    result = load_track("generic-saas")
    assert result["name"] == "Generic SaaS"
    assert "VP of Engineering" in result["titles"]

def test_load_shared_criteria(tmp_path, monkeypatch):
    """load_shared_criteria reads job_criteria.yaml."""
    from src.config import load_shared_criteria
    f = tmp_path / "job_criteria.yaml"
    f.write_text(yaml.dump({"location": {"remote": True, "country": "US"}}))
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    result = load_shared_criteria()
    assert result["location"]["remote"] is True

def test_load_keywords(tmp_path, monkeypatch):
    """load_keywords reads keywords.yaml."""
    from src.config import load_keywords
    f = tmp_path / "keywords.yaml"
    f.write_text(yaml.dump({"exclude": ["contract"], "citizenship_exclude": []}))
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    result = load_keywords()
    assert "contract" in result["exclude"]

def test_save_track_writes_yaml(tmp_path, monkeypatch):
    """save_track writes a track config back to YAML."""
    from src.config import save_track
    track_dir = tmp_path / "tracks"
    track_dir.mkdir()
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    save_track("generic-saas", {"name": "Updated"})
    result = yaml.safe_load((track_dir / "generic-saas.yaml").read_text())
    assert result["name"] == "Updated"

def test_load_schedule(tmp_path, monkeypatch):
    """load_schedule reads schedule.yaml."""
    from src.config import load_schedule
    f = tmp_path / "schedule.yaml"
    f.write_text(yaml.dump({"enabled": False, "hour": 8, "minute": 0}))
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    result = load_schedule()
    assert result["enabled"] is False

def test_load_all_tracks(tmp_path, monkeypatch):
    """load_all_tracks returns a dict keyed by track name."""
    from src.config import load_all_tracks
    track_dir = tmp_path / "tracks"
    track_dir.mkdir()
    (track_dir / "generic-saas.yaml").write_text(yaml.dump({"name": "SaaS"}))
    (track_dir / "data-ai.yaml").write_text(yaml.dump({"name": "Data AI"}))
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    result = load_all_tracks()
    assert "generic-saas" in result
    assert "data-ai" in result
