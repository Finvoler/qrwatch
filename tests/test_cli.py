from qrwatch.cli import main
from pathlib import Path


def test_cli_starts_in_dry_run_mode(capsys):
    assert main([]) == 0

    output = capsys.readouterr().out

    assert "QR Watch started in dry-run mode" in output
    assert "provider=dry-run" in output
    assert "capture=disabled" in output
    assert "notifications_sent=0" in output


def test_cli_capture_once_prints_frame_metadata(monkeypatch, capsys):
    class FakeApp:
        def __init__(self, config):
            self.config = config

        def capture_once(self, *, monitor_index, save_path=None):
            from datetime import datetime, timezone

            from qrwatch.app import RunSummary

            assert monitor_index == 0
            assert save_path is None
            return RunSummary(
                dry_run=True,
                interval_seconds=self.config.interval_seconds,
                notifier_provider=self.config.notifier_provider,
                credential_sources=self.config.credential_sources,
                capture_enabled=True,
                capture_width=1920,
                capture_height=1080,
                capture_source="monitor:0",
                captured_at=datetime(2026, 5, 9, tzinfo=timezone.utc),
                qr_detection_enabled=True,
                qr_detections_count=2,
            )

    monkeypatch.setattr("qrwatch.cli.QRWatchApp", FakeApp)

    assert main(["--capture-once", "--monitor", "0"]) == 0

    output = capsys.readouterr().out

    assert "capture=enabled" in output
    assert "capture_source=monitor:0" in output
    assert "capture_size=1920x1080" in output
    assert "captured_at=2026-05-09T00:00:00+00:00" in output
    assert "qr_detection=enabled" in output
    assert "qr_detections=2" in output
    assert "notifications_sent=0" in output


def test_cli_save_capture_prints_saved_path(monkeypatch, capsys):
    output_path = Path("capture.png")

    class FakeApp:
        def __init__(self, config):
            self.config = config

        def capture_once(self, *, monitor_index, save_path=None):
            from datetime import datetime, timezone

            from qrwatch.app import RunSummary

            assert monitor_index == 1
            assert save_path == output_path
            return RunSummary(
                dry_run=True,
                interval_seconds=self.config.interval_seconds,
                notifier_provider=self.config.notifier_provider,
                credential_sources=self.config.credential_sources,
                capture_enabled=True,
                capture_width=800,
                capture_height=600,
                capture_source="monitor:1",
                captured_at=datetime(2026, 5, 9, tzinfo=timezone.utc),
                capture_saved_path=output_path,
                qr_detection_enabled=True,
                qr_detections_count=0,
            )

    monkeypatch.setattr("qrwatch.cli.QRWatchApp", FakeApp)

    assert main(["--save-capture", str(output_path)]) == 0

    output = capsys.readouterr().out

    assert "capture=enabled" in output
    assert f"capture_saved={output_path}" in output
    assert "qr_detections=0" in output


def test_cli_applies_deduplication_options(monkeypatch):
    state_path = Path("artifacts/test-state/cli-state.json")

    class FakeApp:
        def __init__(self, config):
            assert config.dedup_window_seconds == 42.0
            assert config.state_path == state_path
            self.config = config

        def run_once(self):
            from qrwatch.app import RunSummary

            return RunSummary(
                dry_run=True,
                interval_seconds=self.config.interval_seconds,
                notifier_provider=self.config.notifier_provider,
                credential_sources=self.config.credential_sources,
            )

    monkeypatch.setattr("qrwatch.cli.QRWatchApp", FakeApp)

    assert main(["--dedup-window", "42", "--state-path", str(state_path)]) == 0


def test_cli_applies_screenshot_retention_options(monkeypatch):
    screenshot_dir = Path("artifacts/test-screenshots/cli-retention")

    class FakeApp:
        def __init__(self, config):
            assert config.save_screenshots is True
            assert config.screenshot_dir == screenshot_dir
            assert config.screenshot_max_count == 5
            assert config.screenshot_max_age_days == 0.5
            self.config = config

        def run_once(self):
            from qrwatch.app import RunSummary

            return RunSummary(
                dry_run=True,
                interval_seconds=self.config.interval_seconds,
                notifier_provider=self.config.notifier_provider,
                credential_sources=self.config.credential_sources,
            )

    monkeypatch.setattr("qrwatch.cli.QRWatchApp", FakeApp)

    assert (
        main(
            [
                "--save-screenshots",
                "--screenshot-dir",
                str(screenshot_dir),
                "--screenshot-max-count",
                "5",
                "--screenshot-max-age-days",
                "0.5",
            ]
        )
        == 0
    )


def test_cli_run_starts_background_controller(monkeypatch):
    import qrwatch.background
    import qrwatch.logging

    log_dir = Path("artifacts/test-logs/cli-run")
    calls = []

    def fake_configure_logging(log_dir, *, level="INFO", console=True):
        calls.append((log_dir, level, console))
        return Path(log_dir) / "qrwatch.log"

    class FakeController:
        def __init__(self, app):
            self.app = app

        def run_forever(self):
            assert self.app.config.monitor_index == 0
            assert self.app.config.log_dir == log_dir
            return 0

    monkeypatch.setattr(qrwatch.logging, "configure_logging", fake_configure_logging)
    monkeypatch.setattr(qrwatch.background, "BackgroundController", FakeController)

    assert main(["--run", "--monitor", "0", "--log-dir", str(log_dir)]) == 0
    assert calls == [(log_dir, "INFO", True)]


def test_cli_tray_delegates_to_tray_entrypoint(monkeypatch):
    import qrwatch.tray

    screenshot_dir = Path("artifacts/test-screenshots/cli-tray")
    calls = []

    def fake_run_tray(config, *, monitor_index=None):
        calls.append((config.screenshot_dir, monitor_index))
        return 0

    monkeypatch.setattr(qrwatch.tray, "run_tray", fake_run_tray)

    assert (
        main(
            [
                "--tray",
                "--monitor",
                "0",
                "--screenshot-dir",
                str(screenshot_dir),
            ]
        )
        == 0
    )
    assert calls == [(screenshot_dir, 0)]


def test_cli_packaged_defaults_to_tray_and_default_config(monkeypatch):
    import qrwatch.tray

    calls = []
    local_app_data = Path("artifacts/test-localappdata/cli-packaged")
    config_path = local_app_data / "QRWatch" / "config.env"
    if config_path.exists():
        config_path.unlink()

    def fake_run_tray(config, *, monitor_index=None):
        calls.append((config.config_path, config.dry_run, monitor_index))
        return 0

    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))
    monkeypatch.setattr(qrwatch.tray, "run_tray", fake_run_tray)

    assert (
        main(
            [],
            use_default_config_file=True,
            create_default_config=True,
            default_tray=True,
        )
        == 0
    )

    assert calls == [(config_path, True, 1)]
    assert config_path.exists()
