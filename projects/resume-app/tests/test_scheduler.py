# tests/test_scheduler.py
from unittest.mock import patch, MagicMock
import pytest

def test_set_schedule_enabled():
    from src import scheduler as sched_module
    with patch.object(sched_module.scheduler, "remove_all_jobs") as mock_remove:
        with patch.object(sched_module.scheduler, "add_job") as mock_add:
            with patch("src.scheduler.save_schedule") as mock_save:
                sched_module.set_schedule(hour=8, minute=0, enabled=True, tracks="all")
                mock_remove.assert_called_once()
                mock_add.assert_called_once()
                mock_save.assert_called_once()

def test_set_schedule_disabled():
    from src import scheduler as sched_module
    with patch.object(sched_module.scheduler, "remove_all_jobs") as mock_remove:
        with patch("src.scheduler.save_schedule") as mock_save:
            sched_module.set_schedule(hour=8, minute=0, enabled=False)
            mock_remove.assert_called_once()
            mock_save.assert_called_once()

def test_get_schedule_status_keys():
    from src.scheduler import get_schedule_status
    with patch("src.scheduler.load_schedule", return_value={
        "enabled": True, "hour": 8, "minute": 0,
        "timezone": "America/New_York", "tracks": "all"
    }):
        with patch("src.scheduler.scheduler") as mock_sched:
            mock_sched.get_job.return_value = None
            status = get_schedule_status()
            assert "enabled" in status
            assert "hour" in status
            assert "next_run" in status
