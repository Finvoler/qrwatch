"""Background worker lifecycle for QR Watch."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from qrwatch.app import QRWatchApp, RunSummary
from qrwatch.logging import redact_error

LOGGER = logging.getLogger("qrwatch.background")

STATUS_STOPPED = "stopped"
STATUS_RUNNING = "running"
STATUS_PAUSED = "paused"
STATUS_DEGRADED = "degraded"


@dataclass(frozen=True)
class RuntimeFolders:
    log_dir: Path
    screenshot_dir: Path


class BackgroundController:
    """Own the long-lived screenshot loop and user-facing lifecycle controls."""

    def __init__(
        self,
        app: QRWatchApp,
        *,
        monitor_index: int | None = None,
        interval_seconds: float | None = None,
    ) -> None:
        self.app = app
        self.monitor_index = (
            app.config.monitor_index if monitor_index is None else monitor_index
        )
        self.interval_seconds = (
            app.config.interval_seconds
            if interval_seconds is None
            else interval_seconds
        )
        self.folders = RuntimeFolders(
            log_dir=app.config.log_dir,
            screenshot_dir=app.config.screenshot_dir,
        )
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._status = STATUS_STOPPED
        self.last_summary: RunSummary | None = None
        self.last_error: str | None = None

    @property
    def status(self) -> str:
        with self._lock:
            return self._status

    @property
    def is_alive(self) -> bool:
        thread = self._thread
        return thread is not None and thread.is_alive()

    def start(self) -> None:
        """Start monitoring if the worker is not already running."""

        if self.is_alive:
            self.resume()
            return

        self._stop_event.clear()
        self._pause_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="qrwatch-background",
            daemon=True,
        )
        self._thread.start()

    def pause(self) -> None:
        """Pause capture and notification work while keeping the process alive."""

        if self.is_alive:
            self._pause_event.set()
            self._set_status(STATUS_PAUSED)
            LOGGER.info("background monitoring paused")

    def resume(self) -> None:
        """Resume monitoring or start it if it is stopped."""

        if not self.is_alive:
            self.start()
            return
        self._pause_event.clear()
        self._set_status(STATUS_RUNNING)
        LOGGER.info("background monitoring resumed")

    def stop(self, *, timeout: float = 5.0) -> None:
        """Request clean shutdown and wait briefly for the worker to exit."""

        self._stop_event.set()
        self._pause_event.clear()
        thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(timeout=timeout)
        self._set_status(STATUS_STOPPED)
        LOGGER.info("background monitoring stopped")

    def capture_now(self) -> RunSummary | None:
        """Run one capture cycle immediately from a UI action."""

        try:
            summary = self.app.capture_once(monitor_index=self.monitor_index)
        except Exception as exc:
            self.last_error = redact_error(exc, self._secret_values())
            self._set_status(STATUS_DEGRADED)
            LOGGER.error("capture once failed error=%s", self.last_error)
            return None

        self.last_summary = summary
        self.last_error = None
        log_run_summary(summary, prefix="manual capture completed")
        return summary

    def run_forever(self) -> int:
        """Run until interrupted by Ctrl+C or an external stop request."""

        self.start()
        try:
            while self.is_alive:
                thread = self._thread
                if thread is None:
                    break
                thread.join(timeout=0.2)
        except KeyboardInterrupt:
            LOGGER.info("shutdown requested by keyboard interrupt")
        finally:
            self.stop()
        return 0

    def _run_loop(self) -> None:
        self._set_status(STATUS_RUNNING)
        if hasattr(self.app, "prune_screenshots"):
            try:
                self.app.prune_screenshots()
            except Exception as exc:
                self.last_error = redact_error(exc, self._secret_values())
                self._set_status(STATUS_DEGRADED)
                LOGGER.warning(
                    "screenshot retention cleanup failed error=%s",
                    self.last_error,
                )

        LOGGER.info(
            "background monitoring started provider=%s dry_run=%s "
            "interval_seconds=%s monitor_index=%s log_dir=%s screenshot_dir=%s",
            self.app.config.notifier_provider,
            self.app.config.dry_run,
            self.interval_seconds,
            self.monitor_index,
            self.folders.log_dir,
            self.folders.screenshot_dir,
        )

        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                self._stop_event.wait(0.2)
                continue

            if self.status != STATUS_RUNNING:
                self._set_status(STATUS_RUNNING)

            try:
                summary = self.app.capture_once(monitor_index=self.monitor_index)
            except Exception as exc:
                self.last_error = redact_error(exc, self._secret_values())
                self._set_status(STATUS_DEGRADED)
                LOGGER.error("background cycle failed error=%s", self.last_error)
            else:
                self.last_summary = summary
                self.last_error = None
                log_run_summary(summary, prefix="background cycle completed")

            self._stop_event.wait(self.interval_seconds)

        self._set_status(STATUS_STOPPED)
        LOGGER.info("background monitoring loop exited cleanly")

    def _set_status(self, status: str) -> None:
        with self._lock:
            self._status = status

    def _secret_values(self) -> tuple[str | None, ...]:
        config = self.app.config
        return (
            config.smtp_username,
            config.smtp_password,
            config.notify_from,
            config.notify_to,
        )


def log_run_summary(summary: RunSummary, *, prefix: str) -> None:
    """Log one cycle summary without QR payload contents."""

    LOGGER.info(
        "%s source=%s size=%sx%s qr_detections=%s qr_events=%s "
        "notification_events=%s suppressed_events=%s notifications_sent=%s "
        "notifications_failed=%s",
        prefix,
        summary.capture_source,
        summary.capture_width,
        summary.capture_height,
        summary.qr_detections_count,
        summary.qr_events_count,
        summary.notification_events_count,
        summary.suppressed_events_count,
        summary.notifications_sent,
        summary.notifications_failed,
    )
