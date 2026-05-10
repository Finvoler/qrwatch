"""Command-line interface for QR Watch."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
from typing import Sequence

from qrwatch.app import QRWatchApp
from qrwatch.capture import CaptureBackendUnavailable, CaptureError
from qrwatch.config import (
    ConfigError,
    load_config,
    parse_credential_sources,
    parse_dedup_window,
    parse_non_negative_int,
    parse_positive_float,
    parse_positive_int,
)
from qrwatch.detectors import DetectorBackendUnavailable, QRDetectionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qrwatch",
        description="Run the QR Watch local watcher.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a local dotenv-style QR Watch config file.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        help="Screenshot interval in seconds.",
    )
    parser.add_argument(
        "--provider",
        help="Notifier provider name, such as dry-run, email, webhook, qq, or wechat.",
    )
    parser.add_argument(
        "--credential-sources",
        help="Comma-separated credential source names, such as env or local-file.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Run the continuous background screenshot loop until stopped.",
    )
    parser.add_argument(
        "--tray",
        action="store_true",
        help="Start the Windows user-session system tray process.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        dest="capture_once",
        help="Alias for --capture-once.",
    )
    parser.add_argument(
        "--capture-once",
        action="store_true",
        help="Capture one screen frame and print metadata without saving it.",
    )
    parser.add_argument(
        "--save-capture",
        type=Path,
        metavar="PATH",
        help="Save one captured frame as a PNG at PATH; implies --capture-once.",
    )
    parser.add_argument(
        "--monitor",
        type=int,
        help="mss monitor index to capture; use 1 for primary or 0 for all monitors.",
    )
    parser.add_argument(
        "--dedup-window",
        help="Seconds to suppress repeated QR payload notifications.",
    )
    parser.add_argument(
        "--state-path",
        type=Path,
        help="Path to the local JSON deduplication state file.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        help="Directory for local QR Watch logs.",
    )
    parser.add_argument(
        "--screenshot-dir",
        type=Path,
        help="Directory opened by tray screenshot controls.",
    )
    parser.add_argument(
        "--save-screenshots",
        action="store_true",
        default=None,
        help="Retain captured screenshots under the configured screenshot directory.",
    )
    parser.add_argument(
        "--no-save-screenshots",
        action="store_false",
        dest="save_screenshots",
        help="Disable automatic screenshot retention.",
    )
    parser.add_argument(
        "--screenshot-max-count",
        help="Maximum retained screenshots in the screenshot directory.",
    )
    parser.add_argument(
        "--screenshot-max-age-days",
        help="Maximum retained screenshot age in days.",
    )
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Log verbosity for background and tray runs.",
    )
    dry_run = parser.add_mutually_exclusive_group()
    dry_run.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Force dry-run mode.",
    )
    dry_run.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Disable dry-run mode after a real provider is implemented.",
    )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    use_default_config_file: bool = False,
    create_default_config: bool = False,
    default_tray: bool = False,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if default_tray and not _has_explicit_mode(args):
        args.tray = True

    try:
        config = load_config(
            config_path=args.config,
            use_default_config_file=use_default_config_file,
            create_default_config=create_default_config,
        )
        if args.interval is not None:
            config = replace(config, interval_seconds=args.interval).validated()
        if args.provider is not None:
            config = replace(config, notifier_provider=args.provider).validated()
        if args.credential_sources is not None:
            config = replace(
                config,
                credential_sources=parse_credential_sources(args.credential_sources),
            ).validated()
        if args.dedup_window is not None:
            config = replace(
                config,
                dedup_window_seconds=parse_dedup_window(args.dedup_window),
            ).validated()
        if args.state_path is not None:
            config = replace(config, state_path=args.state_path).validated()
        if args.log_dir is not None:
            config = replace(config, log_dir=args.log_dir).validated()
        if args.screenshot_dir is not None:
            config = replace(config, screenshot_dir=args.screenshot_dir).validated()
        if args.save_screenshots is not None:
            config = replace(
                config,
                save_screenshots=args.save_screenshots,
            ).validated()
        if args.screenshot_max_count is not None:
            config = replace(
                config,
                screenshot_max_count=parse_positive_int(
                    args.screenshot_max_count,
                    name="screenshot max count",
                ),
            ).validated()
        if args.screenshot_max_age_days is not None:
            config = replace(
                config,
                screenshot_max_age_days=parse_positive_float(
                    args.screenshot_max_age_days,
                    name="screenshot max age",
                ),
            ).validated()
        if args.log_level is not None:
            config = replace(config, log_level=args.log_level).validated()
        if args.monitor is not None:
            config = replace(
                config,
                monitor_index=parse_non_negative_int(
                    str(args.monitor),
                    name="monitor index",
                ),
            ).validated()
        if args.dry_run is not None:
            config = replace(config, dry_run=args.dry_run).validated()

        if args.run and args.tray:
            parser.error("--run and --tray cannot be used together")
        if (args.run or args.tray) and args.save_capture is not None:
            parser.error("--save-capture is only supported with --capture-once")

        app = QRWatchApp(config)
        if args.tray:
            from qrwatch.tray import run_tray

            return run_tray(config, monitor_index=config.monitor_index)
        if args.run:
            from qrwatch.background import BackgroundController
            from qrwatch.logging import configure_logging

            configure_logging(config.log_dir, level=config.log_level)
            controller = BackgroundController(app)
            return controller.run_forever()
        if args.capture_once or args.save_capture is not None:
            summary = app.capture_once(
                monitor_index=config.monitor_index,
                save_path=args.save_capture,
            )
        else:
            summary = app.run_once()
    except ConfigError as exc:
        parser.error(str(exc))
        return 2
    except (
        CaptureBackendUnavailable,
        CaptureError,
        DetectorBackendUnavailable,
        QRDetectionError,
    ) as exc:
        parser.error(str(exc))
        return 2

    mode = "dry-run" if summary.dry_run else "live"
    print(f"QR Watch started in {mode} mode")
    print(f"provider={summary.notifier_provider}")
    print(f"interval_seconds={summary.interval_seconds:g}")
    print(f"credential_sources={','.join(summary.credential_sources)}")
    if summary.capture_enabled:
        print("capture=enabled")
        print(f"capture_source={summary.capture_source}")
        print(f"capture_size={summary.capture_width}x{summary.capture_height}")
        if summary.captured_at is not None:
            print(f"captured_at={summary.captured_at.isoformat()}")
        if summary.capture_saved_path is not None:
            print(f"capture_saved={summary.capture_saved_path}")
        print(
            "qr_detection=enabled"
            if summary.qr_detection_enabled
            else "qr_detection=disabled"
        )
        print(f"qr_detections={summary.qr_detections_count}")
        print(f"qr_events={summary.qr_events_count}")
        print(f"notification_events={summary.notification_events_count}")
        print(f"suppressed_events={summary.suppressed_events_count}")
    else:
        print("capture=disabled")
    print(f"notifications_sent={summary.notifications_sent}")
    print(f"notifications_failed={summary.notifications_failed}")
    return 0


def _has_explicit_mode(args: argparse.Namespace) -> bool:
    return bool(
        args.run
        or args.tray
        or args.capture_once
        or args.save_capture is not None
    )
