"""SMTP email notifier."""

from __future__ import annotations

import logging
import smtplib
from collections.abc import Callable
from dataclasses import dataclass, field
from email.message import EmailMessage
from typing import Any

from qrwatch.events import QREvent
from qrwatch.notifiers.base import NotificationResult

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailNotifier:
    provider_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str = field(repr=False)
    notify_to: str
    notify_from: str | None = None
    smtp_use_ssl: bool = True
    smtp_timeout_seconds: float = 10.0
    smtp_ssl_factory: Callable[..., Any] = field(
        default=smtplib.SMTP_SSL,
        repr=False,
        compare=False,
    )
    smtp_factory: Callable[..., Any] = field(
        default=smtplib.SMTP,
        repr=False,
        compare=False,
    )

    def notify(self, event: QREvent) -> NotificationResult:
        message = self._build_message(event)
        try:
            if self.smtp_use_ssl:
                with self.smtp_ssl_factory(
                    self.smtp_host,
                    self.smtp_port,
                    timeout=self.smtp_timeout_seconds,
                ) as smtp:
                    smtp.login(self.smtp_username, self.smtp_password)
                    smtp.send_message(message)
            else:
                with self.smtp_factory(
                    self.smtp_host,
                    self.smtp_port,
                    timeout=self.smtp_timeout_seconds,
                ) as smtp:
                    smtp.starttls()
                    smtp.login(self.smtp_username, self.smtp_password)
                    smtp.send_message(message)
        except Exception as exc:  # pragma: no cover - exact SMTP errors vary.
            LOGGER.warning(
                "email notification failed provider=%s payload_hash=%s error_type=%s",
                self.provider_name,
                event.payload_hash,
                exc.__class__.__name__,
            )
            return NotificationResult(
                provider_name=self.provider_name,
                sent=False,
                dry_run=False,
                payload_hash=event.payload_hash,
                payload_length=len(event.payload),
                error=exc.__class__.__name__,
            )

        LOGGER.info(
            "email notification sent provider=%s payload_hash=%s payload_length=%s",
            self.provider_name,
            event.payload_hash,
            len(event.payload),
        )
        return NotificationResult(
            provider_name=self.provider_name,
            sent=True,
            dry_run=False,
            payload_hash=event.payload_hash,
            payload_length=len(event.payload),
        )

    def notify_dry_run(self) -> NotificationResult:
        return NotificationResult(
            provider_name=self.provider_name,
            sent=False,
            dry_run=True,
        )

    def _build_message(self, event: QREvent) -> EmailMessage:
        message = EmailMessage()
        message["Subject"] = "QR Watch detected a QR code"
        message["From"] = self.notify_from or self.smtp_username
        message["To"] = self.notify_to
        message.set_content(
            "\n".join(
                (
                    "QR Watch detected a QR code.",
                    "",
                    f"Detected at: {event.detected_at.isoformat()}",
                    f"Source: {event.source}",
                    f"Payload hash: {event.payload_hash}",
                    "",
                    "Payload:",
                    event.payload,
                )
            )
        )
        return message
