# tests/test_logger.py
import pytest
import json
from pathlib import Path

def test_log_event_appends():
    from src.logger import RunLogger
    lg = RunLogger()
    lg.log_event("run started")
    assert "run started" in lg.get_all()["events"][0]

def test_log_llm_appends():
    from src.logger import RunLogger
    lg = RunLogger()
    lg.log_llm("job A: KEEP score=82")
    assert "KEEP" in lg.get_all()["llm"][0]

def test_log_debug_appends():
    from src.logger import RunLogger
    lg = RunLogger()
    lg.log_debug("navigating to linkedin")
    assert "linkedin" in lg.get_all()["debug"][0]

def test_clear_resets_all():
    from src.logger import RunLogger
    lg = RunLogger()
    lg.log_event("x")
    lg.log_llm("y")
    lg.log_debug("z")
    lg.clear()
    result = lg.get_all()
    assert result["events"] == []
    assert result["llm"] == []
    assert result["debug"] == []

def test_save_and_load(tmp_path, monkeypatch):
    from src.logger import RunLogger
    monkeypatch.setenv("LOG_DIR", str(tmp_path))
    lg = RunLogger()
    lg.log_event("started")
    lg.log_llm("job KEEP")
    lg.save("2026-08-27-0800")
    loaded = lg.load("2026-08-27-0800")
    assert "started" in loaded["events"][0]
    assert "KEEP" in loaded["llm"][0]

def test_timestamps_included():
    from src.logger import RunLogger
    import re
    lg = RunLogger()
    lg.log_event("test message")
    entry = lg.get_all()["events"][0]
    assert re.search(r'\[\d{2}:\d{2}:\d{2}\]', entry)
