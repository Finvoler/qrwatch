from __future__ import annotations

import logging
from datetime import datetime, timezone

from qrwatch.config import ConfigError, load_config
from qrwatch.events import QREvent, hash_payload
from qrwatch.notifiers import EmailNotifier as ExportedEmailNotifier
from qrwatch.notifiers import create_notifier
from qrwatch.notifiers.base import DryRunNotifier
from qrwatch.notifiers.email import EmailNotifier


def make_event() -> QREvent:
    payload = "https://example.test/qr-secret"
    return QREvent(
        payload=payload,
        payload_hash=hash_payload(payload),
        source="fixture:screen",
        detected_at=datetime(2026, 5, 10, 12, tzinfo=timezone.utc),
    )


def test_dry_run_notifier_returns_redacted_metadata(caplog):
    event = make_event()
    notifier = DryRunNotifier(provider_name="email")
    caplog.set_level(logging.INFO)

    result = notifier.notify(event)

    assert result.sent is False
    assert result.dry_run is True
    assert result.payload_hash == event.payload_hash
    assert result.payload_length == len(event.payload)
    assert event.payload not in caplog.text


def test_email_notifier_sends_qr_payload_with_fake_smtp():
    smtp_calls = []

    class FakeSMTP:
        def __init__(self, host, port, *, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout
            self.messages = []
            smtp_calls.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, username, password):
            self.username = username
            self.password = password

        def send_message(self, message):
            self.messages.append(message)

    event = make_event()
    notifier = EmailNotifier(
        provider_name="qq-mail",
        smtp_host="smtp.qq.com",
        smtp_port=465,
        smtp_username="sender@qq.com",
        smtp_password="authorization-code",
        notify_to="receiver@example.com",
        smtp_ssl_factory=FakeSMTP,
    )

    result = notifier.notify(event)

    assert result.sent is True
    assert result.dry_run is False
    assert len(smtp_calls) == 1
    assert smtp_calls[0].host == "smtp.qq.com"
    assert smtp_calls[0].port == 465
    assert smtp_calls[0].username == "sender@qq.com"
    assert smtp_calls[0].password == "authorization-code"
    message = smtp_calls[0].messages[0]
    assert message["From"] == "sender@qq.com"
    assert message["To"] == "receiver@example.com"
    assert event.payload in message.get_content()
    assert event.payload_hash in message.get_content()


def test_email_notifier_reports_smtp_failure_without_secret(caplog):
    class FailingSMTP:
        def __init__(self, host, port, *, timeout):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def login(self, username, password):
            raise RuntimeError(f"bad password {password}")

    notifier = EmailNotifier(
        provider_name="qq-mail",
        smtp_host="smtp.qq.com",
        smtp_port=465,
        smtp_username="sender@qq.com",
        smtp_password="authorization-code",
        notify_to="receiver@example.com",
        smtp_ssl_factory=FailingSMTP,
    )
    caplog.set_level(logging.WARNING)

    result = notifier.notify(make_event())

    assert result.sent is False
    assert result.error == "RuntimeError"
    assert "authorization-code" not in result.error
    assert "authorization-code" not in caplog.text


def test_create_notifier_returns_dry_run_while_config_is_dry_run():
    config = load_config(
        env={
            "QRWATCH_NOTIFY_PROVIDER": "qq-mail",
            "QRWATCH_DRY_RUN": "true",
        }
    )

    notifier = create_notifier(config)

    assert isinstance(notifier, DryRunNotifier)
    assert notifier.provider_name == "qq-mail"


def test_create_notifier_returns_email_for_live_qq_mail():
    config = load_config(
        env={
            "QRWATCH_NOTIFY_PROVIDER": "qq-mail",
            "QRWATCH_DRY_RUN": "false",
            "QRWATCH_SMTP_USERNAME": "sender@qq.com",
            "QRWATCH_SMTP_PASSWORD": "authorization-code",
            "QRWATCH_NOTIFY_TO": "receiver@example.com",
        }
    )

    notifier = create_notifier(config)

    assert isinstance(notifier, ExportedEmailNotifier)
    assert notifier.smtp_host == "smtp.qq.com"
    assert notifier.smtp_port == 465


def test_create_notifier_rejects_unsupported_live_provider():
    config = load_config(
        env={
            "QRWATCH_NOTIFY_PROVIDER": "webhook",
            "QRWATCH_DRY_RUN": "false",
        }
    )

    try:
        create_notifier(config)
    except ConfigError as exc:
        assert "unsupported live notifier provider" in str(exc)
    else:
        raise AssertionError("expected unsupported live provider to fail")
