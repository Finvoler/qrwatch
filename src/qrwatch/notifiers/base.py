"""Notifier provider interfaces."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Protocol

from qrwatch.events import QREvent

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class NotificationResult:
    provider_name: str
    sent: bool
    dry_run: bool
    payload_hash: str | None = None
    payload_length: int | None = None
    error: str | None = None


class Notifier(Protocol):
    provider_name: str

    def notify(self, event: QREvent) -> NotificationResult:
        """Dispatch one notification event."""

    def notify_dry_run(self) -> NotificationResult:
        """Exercise notifier composition without sending anything."""


@dataclass(frozen=True)
class DryRunNotifier:
    provider_name: str = "dry-run"

    def notify(self, event: QREvent) -> NotificationResult:
        LOGGER.info(
            "dry-run notification provider=%s payload_hash=%s payload_length=%s "
            "source=%s detected_at=%s",
            self.provider_name,
            event.payload_hash,
            len(event.payload),
            event.source,
            event.detected_at.isoformat(),
        )
        return NotificationResult(
            provider_name=self.provider_name,
            sent=False,
            dry_run=True,
            payload_hash=event.payload_hash,
            payload_length=len(event.payload),
        )

    def notify_dry_run(self) -> NotificationResult:
        LOGGER.info("dry-run notifier provider=%s composed", self.provider_name)
        return NotificationResult(
            provider_name=self.provider_name,
            sent=False,
            dry_run=True,
        )
