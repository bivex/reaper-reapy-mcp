"""
Root conftest.py — shared fixtures and markers for all tests.

Integration tests that require a live REAPER connection are marked with
@pytest.mark.reaper and skipped automatically when REAPER is not running.

Run integration tests explicitly:
    pytest -m reaper
"""
import socket
import warnings
import pytest


def _reaper_is_running() -> bool:
    """Return True if the reapy server is reachable."""
    for port in [2306, 2307, 2308, 2309]:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            result = s.connect_ex(("localhost", port))
            s.close()
            if result == 0:
                return True
        except Exception:
            pass
    return False


REAPER_RUNNING = _reaper_is_running()


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "reaper: mark test as requiring a live REAPER connection"
    )


def pytest_collection_modifyitems(config, items):
    """Skip reaper-marked tests when REAPER is not running."""
    if REAPER_RUNNING:
        return
    skip = pytest.mark.skip(reason="REAPER not running (no server on ports 2306-2309)")
    for item in items:
        if "reaper" in item.keywords:
            item.add_marker(skip)
