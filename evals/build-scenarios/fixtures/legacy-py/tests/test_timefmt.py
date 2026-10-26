from datetime import datetime

from app.timefmt import format_dt


def test_format_dt():
    assert format_dt(datetime(2026, 10, 26, 14, 30)) == "2026-10-26 14:30"
