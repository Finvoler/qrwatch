"""Deduplication state and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from qrwatch.events import QREvent


STATE_VERSION = 1


@dataclass(frozen=True)
class DeduplicationDecision:
    event: QREvent
    payload_seen_before: bool
    should_notify: bool
    reason: str


@dataclass(frozen=True)
class DeduplicationResult:
    decisions: tuple[DeduplicationDecision, ...]

    @property
    def notification_events(self) -> tuple[QREvent, ...]:
        return tuple(
            decision.event for decision in self.decisions if decision.should_notify
        )

    @property
    def suppressed_events(self) -> tuple[QREvent, ...]:
        return tuple(
            decision.event for decision in self.decisions if not decision.should_notify
        )


class DeduplicationStateError(RuntimeError):
    """Raised when deduplication state cannot be loaded or saved."""


class JsonDeduplicationStore:
    """Small JSON store keyed by QR payload hash."""

    def __init__(self, path: str | Path, *, window_seconds: float) -> None:
        if window_seconds <= 0:
            raise ValueError("deduplication window must be greater than zero seconds")
        self.path = Path(path)
        self.window = timedelta(seconds=window_seconds)

    def filter_events(self, events: tuple[QREvent, ...]) -> DeduplicationResult:
        """Return per-event notify/suppress decisions and persist updated state."""

        if not events:
            return DeduplicationResult(decisions=())

        state = self._load()
        entries = state.setdefault("entries", {})
        decisions: list[DeduplicationDecision] = []

        for event in events:
            payload_hash = event.payload_hash
            existing = entries.get(payload_hash)
            payload_seen_before = existing is not None
            should_notify = self._should_notify(existing, event.detected_at)
            reason = _decision_reason(payload_seen_before, should_notify)

            entries[payload_hash] = self._updated_entry(
                existing,
                event.detected_at,
                should_notify=should_notify,
            )
            decisions.append(
                DeduplicationDecision(
                    event=event,
                    payload_seen_before=payload_seen_before,
                    should_notify=should_notify,
                    reason=reason,
                )
            )

        self._save(state)
        return DeduplicationResult(decisions=tuple(decisions))

    def _should_notify(self, entry: dict[str, Any] | None, detected_at: datetime) -> bool:
        if entry is None:
            return True

        last_notified_at = _parse_datetime(entry.get("last_notified_at"))
        if last_notified_at is None:
            return True

        return detected_at - last_notified_at >= self.window

    def _updated_entry(
        self,
        entry: dict[str, Any] | None,
        detected_at: datetime,
        *,
        should_notify: bool,
    ) -> dict[str, Any]:
        detected_at = _ensure_aware_utc(detected_at)
        first_seen_at = (
            _parse_datetime(entry.get("first_seen_at")) if entry is not None else None
        )
        seen_count = int(entry.get("seen_count", 0)) if entry is not None else 0
        last_notified_at = (
            detected_at
            if should_notify
            else _parse_datetime(entry.get("last_notified_at"))
        )

        return {
            "first_seen_at": _format_datetime(first_seen_at or detected_at),
            "last_seen_at": _format_datetime(detected_at),
            "last_notified_at": (
                _format_datetime(last_notified_at)
                if last_notified_at is not None
                else None
            ),
            "seen_count": seen_count + 1,
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": STATE_VERSION, "entries": {}}

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise DeduplicationStateError(
                f"failed to load deduplication state: {self.path}"
            ) from exc

        if not isinstance(data, dict):
            raise DeduplicationStateError("deduplication state must be a JSON object")
        if data.get("version") != STATE_VERSION:
            raise DeduplicationStateError(
                f"unsupported deduplication state version: {data.get('version')}"
            )
        if not isinstance(data.get("entries"), dict):
            raise DeduplicationStateError("deduplication state entries must be an object")
        return data

    def _save(self, state: dict[str, Any]) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(state, indent=2, sort_keys=True),
                encoding="utf-8",
            )
        except OSError as exc:
            raise DeduplicationStateError(
                f"failed to save deduplication state: {self.path}"
            ) from exc


def _decision_reason(payload_seen_before: bool, should_notify: bool) -> str:
    if should_notify and payload_seen_before:
        return "deduplication window expired"
    if should_notify:
        return "new payload"
    return "suppressed inside deduplication window"


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    return _ensure_aware_utc(datetime.fromisoformat(value))


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _format_datetime(value: datetime) -> str:
    return _ensure_aware_utc(value).isoformat()
