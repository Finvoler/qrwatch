from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator

from qrwatch.storage import prune_screenshots, retained_screenshot_path


NOW = datetime(2026, 5, 10, 12)


@contextmanager
def _screenshot_dir(name: str) -> Iterator[Path]:
    directory = Path("artifacts/test-screenshots") / name
    directory.mkdir(parents=True, exist_ok=True)
    for path in directory.iterdir():
        if path.is_file():
            path.unlink()
    try:
        yield directory
    finally:
        for path in directory.iterdir():
            if path.is_file():
                path.unlink()
        try:
            directory.rmdir()
        except OSError:
            pass


def _screenshot(path, *, age_hours: float) -> None:
    path.write_bytes(b"png")
    timestamp = (NOW - timedelta(hours=age_hours)).timestamp()
    os.utime(path, (timestamp, timestamp))


def test_retained_screenshot_path_uses_timestamp_and_source():
    with _screenshot_dir("path") as directory:
        path = retained_screenshot_path(
            directory,
            captured_at=NOW,
            source="monitor:1",
        )

        assert path.parent == directory
        assert path.name == "qrwatch-20260510T120000000000-monitor-1.png"


def test_prune_screenshots_enforces_age_and_count_limits():
    with _screenshot_dir("prune") as directory:
        old = directory / "old.png"
        newest = directory / "newest.png"
        middle = directory / "middle.png"
        ignored = directory / "notes.txt"
        _screenshot(old, age_hours=30)
        _screenshot(middle, age_hours=2)
        _screenshot(newest, age_hours=1)
        ignored.write_text("keep me", encoding="utf-8")

        summary = prune_screenshots(
            directory,
            max_count=1,
            max_age_days=1,
            now=NOW,
        )

        assert summary.deleted_count == 2
        assert summary.retained_count == 1
        assert not old.exists()
        assert not middle.exists()
        assert newest.exists()
        assert ignored.exists()
