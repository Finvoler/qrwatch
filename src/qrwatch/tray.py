"""System tray entrypoint for QR Watch."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from qrwatch.app import QRWatchApp
from qrwatch.background import BackgroundController, STATUS_PAUSED, STATUS_RUNNING
from qrwatch.config import AppConfig, default_config_path, write_starter_config
from qrwatch.logging import configure_logging


def run_tray(config: AppConfig, *, monitor_index: int | None = None) -> int:
    """Start the QR Watch tray process."""

    try:
        import pystray
        from PIL import Image, ImageDraw
    except ImportError as exc:  # pragma: no cover - depends on runtime environment
        raise RuntimeError(
            "pystray and pillow are required for --tray; install the qrwatch environment"
        ) from exc

    configure_logging(config.log_dir, level=config.log_level, console=False)
    controller = BackgroundController(
        QRWatchApp(config),
        monitor_index=monitor_index,
    )

    def start(icon, item):
        controller.start()
        icon.update_menu()

    def pause(icon, item):
        controller.pause()
        icon.update_menu()

    def resume(icon, item):
        controller.resume()
        icon.update_menu()

    def capture_once(icon, item):
        controller.capture_now()
        icon.update_menu()

    def open_logs(icon, item):
        open_directory(controller.folders.log_dir)

    def open_screenshots(icon, item):
        open_directory(controller.folders.screenshot_dir)

    def open_settings(icon, item):
        settings_path = config.config_path or default_config_path()
        write_starter_config(settings_path)
        open_file(settings_path)

    def exit_app(icon, item):
        controller.stop()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem(
            lambda item: f"Status: {controller.status}",
            None,
            enabled=False,
        ),
        pystray.MenuItem(
            "Start",
            start,
            enabled=lambda item: controller.status != STATUS_RUNNING,
        ),
        pystray.MenuItem(
            "Pause",
            pause,
            enabled=lambda item: controller.status == STATUS_RUNNING,
        ),
        pystray.MenuItem(
            "Resume",
            resume,
            enabled=lambda item: controller.status == STATUS_PAUSED,
        ),
        pystray.MenuItem("Capture once", capture_once),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Open logs", open_logs),
        pystray.MenuItem("Open screenshots", open_screenshots),
        pystray.MenuItem("Open settings file", open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", exit_app),
    )
    icon = pystray.Icon(
        "qrwatch",
        _create_icon_image(Image, ImageDraw),
        "QR Watch",
        menu,
    )
    icon.run()
    return 0


def open_directory(path: str | Path) -> None:
    """Open a local directory in the platform file browser."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    if hasattr(os, "startfile"):
        os.startfile(str(directory))  # type: ignore[attr-defined]
        return
    command = ["open", str(directory)] if sys.platform == "darwin" else ["xdg-open", str(directory)]
    subprocess.Popen(command)


def open_file(path: str | Path) -> None:
    """Open a local file in the platform default editor."""

    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(os, "startfile"):
        os.startfile(str(file_path))  # type: ignore[attr-defined]
        return
    command = ["open", str(file_path)] if sys.platform == "darwin" else ["xdg-open", str(file_path)]
    subprocess.Popen(command)


def _create_icon_image(image_module, draw_module):
    image = image_module.new("RGB", (64, 64), color=(24, 24, 24))
    draw = draw_module.Draw(image)
    draw.rectangle((12, 12, 52, 52), outline=(245, 245, 245), width=4)
    draw.rectangle((20, 20, 30, 30), fill=(245, 245, 245))
    draw.rectangle((34, 20, 44, 30), fill=(245, 245, 245))
    draw.rectangle((20, 34, 30, 44), fill=(245, 245, 245))
    draw.rectangle((36, 36, 44, 44), fill=(62, 190, 120))
    return image
