from __future__ import annotations

import threading
from pathlib import Path

from qrwatch.app import RunSummary
from qrwatch.background import BackgroundController, STATUS_DEGRADED, STATUS_STOPPED
from qrwatch.config import load_config


def test_background_controller_runs_until_stopped():
    local_app_data = Path("artifacts/test-localappdata/background-run")
    config = load_config(
        env={
            "LOCALAPPDATA": str(local_app_data),
            "QRWATCH_INTERVAL_SECONDS": "0.01",
            "QRWATCH_MONITOR_INDEX": "0",
        }
    )
    captured = threading.Event()

    class FakeApp:
        def __init__(self):
            self.config = config
            self.calls = 0

        def capture_once(self, *, monitor_index):
            assert monitor_index == 0
            self.calls += 1
            captured.set()
            return RunSummary(
                dry_run=True,
                interval_seconds=config.interval_seconds,
                notifier_provider=config.notifier_provider,
                credential_sources=config.credential_sources,
                capture_enabled=True,
                capture_width=10,
                capture_height=10,
                capture_source="monitor:0",
                qr_detection_enabled=True,
            )

    app = FakeApp()
    controller = BackgroundController(app)
    controller.start()

    assert captured.wait(1)

    controller.stop()

    assert app.calls >= 1
    assert controller.status == STATUS_STOPPED
    assert controller.last_summary is not None


def test_background_controller_redacts_configured_secrets():
    local_app_data = Path("artifacts/test-localappdata/background-redaction")
    config = load_config(
        env={
            "LOCALAPPDATA": str(local_app_data),
            "QRWATCH_NOTIFY_PROVIDER": "email",
            "QRWATCH_DRY_RUN": "false",
            "QRWATCH_SMTP_USERNAME": "sender@qq.com",
            "QRWATCH_SMTP_PASSWORD": "authorization-code",
            "QRWATCH_NOTIFY_TO": "receiver@example.com",
        }
    )

    class FakeApp:
        def __init__(self):
            self.config = config

        def capture_once(self, *, monitor_index):
            raise RuntimeError("failed for authorization-code")

    controller = BackgroundController(FakeApp())

    assert controller.capture_now() is None
    assert controller.last_error == "failed for [redacted]"


def test_background_controller_marks_degraded_after_capture_failure():
    config = load_config(env={})

    class FakeApp:
        def __init__(self):
            self.config = config

        def capture_once(self, *, monitor_index):
            raise RuntimeError("detector unavailable")

    controller = BackgroundController(FakeApp())

    assert controller.capture_now() is None
    assert controller.status == STATUS_DEGRADED
    assert controller.last_error == "detector unavailable"
