"""Application composition and one-cycle lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from qrwatch.capture import capture_screen, save_frame_png
from qrwatch.config import AppConfig
from qrwatch.detectors import detect_qr_codes
from qrwatch.events import shape_detection_events
from qrwatch.notifiers import create_notifier
from qrwatch.notifiers.base import NotificationResult
from qrwatch.state import JsonDeduplicationStore
from qrwatch.storage import prune_screenshots, retained_screenshot_path


@dataclass(frozen=True)
class RunSummary:
    """Summary of a skeleton run that performs no capture or external sends."""

    dry_run: bool
    interval_seconds: float
    notifier_provider: str
    credential_sources: tuple[str, ...]
    capture_enabled: bool = False
    capture_width: int | None = None
    capture_height: int | None = None
    capture_source: str | None = None
    captured_at: datetime | None = None
    capture_saved_path: Path | None = None
    qr_detection_enabled: bool = False
    qr_detections_count: int = 0
    qr_events_count: int = 0
    notification_events_count: int = 0
    suppressed_events_count: int = 0
    notifications_sent: int = 0
    notifications_failed: int = 0


class QRWatchApp:
    """Compose product layers for one capture/detection/notification cycle."""

    def __init__(self, config: AppConfig, *, state_store=None, notifier=None) -> None:
        self.config = config
        self.notifier = notifier or create_notifier(config)
        self.state_store = state_store or JsonDeduplicationStore(
            config.state_path,
            window_seconds=config.dedup_window_seconds,
        )

    def run_once(self) -> RunSummary:
        """Exercise notifier composition without capturing the screen."""

        result = self.notifier.notify_dry_run()
        return RunSummary(
            dry_run=self.config.dry_run,
            interval_seconds=self.config.interval_seconds,
            notifier_provider=self.config.notifier_provider,
            credential_sources=self.config.credential_sources,
            notifications_sent=1 if result.sent else 0,
            notifications_failed=1 if result.error else 0,
        )

    def capture_once(
        self,
        *,
        monitor_index: int = 1,
        save_path: str | Path | None = None,
    ) -> RunSummary:
        """Capture one screen frame, detect QR codes, and dispatch notifications."""

        frame = capture_screen(monitor_index=monitor_index)
        detections = detect_qr_codes(frame.pixels, source=frame.source)
        events = shape_detection_events(detections, detected_at=frame.captured_at)
        deduplication = self.state_store.filter_events(events)
        notification_results = tuple(
            self.notifier.notify(event)
            for event in deduplication.notification_events
        )
        saved_path = self._save_capture_if_configured(frame, save_path=save_path)
        return RunSummary(
            dry_run=self.config.dry_run,
            interval_seconds=self.config.interval_seconds,
            notifier_provider=self.config.notifier_provider,
            credential_sources=self.config.credential_sources,
            capture_enabled=True,
            capture_width=frame.width,
            capture_height=frame.height,
            capture_source=frame.source,
            captured_at=frame.captured_at,
            capture_saved_path=saved_path,
            qr_detection_enabled=True,
            qr_detections_count=len(detections),
            qr_events_count=len(events),
            notification_events_count=len(deduplication.notification_events),
            suppressed_events_count=len(deduplication.suppressed_events),
            notifications_sent=count_sent(notification_results),
            notifications_failed=count_failed(notification_results),
        )

    def prune_screenshots(self) -> None:
        """Apply configured screenshot retention limits."""

        prune_screenshots(
            self.config.screenshot_dir,
            max_count=self.config.screenshot_max_count,
            max_age_days=self.config.screenshot_max_age_days,
        )

    def _save_capture_if_configured(
        self,
        frame,
        *,
        save_path: str | Path | None,
    ) -> Path | None:
        if save_path is not None:
            return save_frame_png(frame, save_path)
        if not self.config.save_screenshots:
            return None

        path = retained_screenshot_path(
            self.config.screenshot_dir,
            captured_at=frame.captured_at,
            source=frame.source,
        )
        saved_path = save_frame_png(frame, path)
        self.prune_screenshots()
        return saved_path


def count_sent(results: tuple[NotificationResult, ...]) -> int:
    return sum(1 for result in results if result.sent)


def count_failed(results: tuple[NotificationResult, ...]) -> int:
    return sum(1 for result in results if result.error)
