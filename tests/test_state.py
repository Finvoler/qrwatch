from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

from qrwatch.events import QREvent, hash_payload
from qrwatch.state import JsonDeduplicationStore


BASE_TIME = datetime(2026, 5, 10, 12, tzinfo=timezone.utc)


def _event(payload: str, *, seconds: int = 0) -> QREvent:
    return QREvent(
        payload=payload,
        payload_hash=hash_payload(payload),
        source="monitor:1",
        detected_at=BASE_TIME + timedelta(seconds=seconds),
    )


@contextmanager
def _state_path(name: str) -> Iterator[Path]:
    path = Path("artifacts/test-state") / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    try:
        yield path
    finally:
        if path.exists():
            path.unlink()
        try:
            path.parent.rmdir()
        except OSError:
            pass


def test_json_store_notifies_new_payload_and_suppresses_repeat_inside_window():
    with _state_path("repeat.json") as path:
        store = JsonDeduplicationStore(path, window_seconds=60)

        first = store.filter_events((_event("secret-payload"),))
        second = JsonDeduplicationStore(path, window_seconds=60).filter_events(
            (_event("secret-payload", seconds=10),)
        )

        assert len(first.notification_events) == 1
        assert len(first.suppressed_events) == 0
        assert len(second.notification_events) == 0
        assert len(second.suppressed_events) == 1

        raw_state = path.read_text(encoding="utf-8")
        assert "secret-payload" not in raw_state
        assert hash_payload("secret-payload") in raw_state


def test_json_store_restart_suppresses_recent_payload():
    with _state_path("restart.json") as path:
        first_store = JsonDeduplicationStore(path, window_seconds=60)
        first_store.filter_events((_event("restart-secret"),))

        restarted_store = JsonDeduplicationStore(path, window_seconds=60)
        result = restarted_store.filter_events((_event("restart-secret", seconds=5),))

        assert len(result.notification_events) == 0
        assert len(result.suppressed_events) == 1


def test_json_store_notifies_repeat_after_window_expires():
    with _state_path("expiry.json") as path:
        store = JsonDeduplicationStore(path, window_seconds=60)

        store.filter_events((_event("secret-payload"),))
        result = store.filter_events((_event("secret-payload", seconds=61),))

        assert len(result.notification_events) == 1
        assert len(result.suppressed_events) == 0
        assert result.decisions[0].payload_seen_before is True
        assert result.decisions[0].reason == "deduplication window expired"


def test_json_store_handles_multiple_qr_codes_in_one_frame():
    with _state_path("multiple.json") as path:
        store = JsonDeduplicationStore(path, window_seconds=60)

        result = store.filter_events(
            (
                _event("payload-a"),
                _event("payload-b"),
                _event("payload-a"),
            )
        )

        assert [event.payload for event in result.notification_events] == [
            "payload-a",
            "payload-b",
        ]
        assert [event.payload for event in result.suppressed_events] == ["payload-a"]

        state = json.loads(path.read_text(encoding="utf-8"))
        assert state["entries"][hash_payload("payload-a")]["seen_count"] == 2
        assert state["entries"][hash_payload("payload-b")]["seen_count"] == 1
