# Environment

Status: applied.

This repository is being adapted for a Windows background Python app that periodically screenshots the active desktop, detects QR codes, and sends a notification through a pluggable channel such as email, QQ, WeChat, or another provider.

The app source skeleton now exists under `src/qrwatch/`. Environment facts below were established on 2026-05-09 by creating the `qrwatch` Conda environment and installing the starter package set.

## Platform

- Primary OS: Windows.
- Runtime mode: background desktop process. The first implementation should run in the logged-in user session, because Windows services do not automatically have access to the interactive desktop for screenshots.
- Packaging target: PyInstaller Windows executable built from the `qrwatch` Conda environment. Generated build output belongs under ignored `dist/` and `build/` folders.

## Language Runtime

- Language: Python.
- Supported Python version: Python 3.11. The created Conda environment currently resolves to Python 3.11.15.
- Package manager: Conda environment plus `pip` packages recorded in `environment.yml`.
- Version manager: Conda.
- Environment name: `qrwatch`.

## Dependency Installation

- Dependency manifest: `environment.yml`.
- Installed starter packages:
  - `mss`: Windows desktop screenshot capture.
  - `opencv-python`: QR detection through OpenCV's `QRCodeDetector`.
  - `pillow` and `numpy`: image conversion and test fixtures.
  - `python-dotenv`: local environment configuration.
  - `requests`: webhook-style notification adapters.
  - `pystray`: simple Windows system tray controller UI.
  - `pyinstaller`: local Windows executable builds.
  - `pytest`: test runner.

Create the environment from the repository manifest:

```bash
conda env create -f environment.yml
```

The environment already exists on this workstation as `qrwatch`.

## Local Services

- Required local services: none for the first local prototype.
- Optional external services:
  - SMTP mailbox provider for email notifications. The first implemented real
    provider is QQ Mail-compatible SMTP.
  - QQ, WeChat, or webhook bridge provider if selected.
- Service credentials: must be provided by the human through local environment variables or a local ignored config file. Do not commit credentials.

## Ports

- No local ports are reserved by the current design.
- If a webhook receiver, local health server, or tray-control HTTP endpoint is added later, document its port and conflict policy here.

## Environment Variables

No variables are required for the default dry-run startup. The current package skeleton recognizes:

- `QRWATCH_INTERVAL_SECONDS`: screenshot interval.
- `QRWATCH_NOTIFY_PROVIDER`: selected notifier, such as `dry-run`, `email`, `qq`, `wechat`, or `webhook`.
- `QRWATCH_DRY_RUN`: dry-run mode flag, such as `true` or `false`.
- `QRWATCH_CREDENTIAL_SOURCES`: comma-separated credential source labels, such as `env` or `local-file`.
- `QRWATCH_CONFIG_FILE`: optional dotenv-style local config file path. Packaged runs default to `%LOCALAPPDATA%\QRWatch\config.env` when this is unset.
- `QRWATCH_DEDUP_WINDOW_SECONDS`: repeated QR payload suppression window, defaulting to 300 seconds.
- `QRWATCH_STATE_PATH`: optional local JSON deduplication state path, defaulting to `%LOCALAPPDATA%\QRWatch\dedup-state.json`.
- `QRWATCH_MONITOR_INDEX`: mss monitor index, defaulting to `1` for the primary monitor; use `0` for all monitors.
- `QRWATCH_LOG_DIR`: optional log directory, defaulting to `%LOCALAPPDATA%\QRWatch\logs`.
- `QRWATCH_SCREENSHOT_DIR`: optional screenshot folder opened by tray controls, defaulting to `%LOCALAPPDATA%\QRWatch\screenshots`.
- `QRWATCH_SAVE_SCREENSHOTS`: whether capture cycles retain screenshots automatically; defaults to `false`.
- `QRWATCH_SCREENSHOT_MAX_COUNT`: maximum retained screenshots, defaulting to `200`.
- `QRWATCH_SCREENSHOT_MAX_AGE_DAYS`: maximum retained screenshot age in days, defaulting to `1`.
- `QRWATCH_LOG_LEVEL`: `DEBUG`, `INFO`, `WARNING`, or `ERROR`; defaults to `INFO`.
- `QRWATCH_SMTP_HOST`: SMTP host, defaulting to `smtp.qq.com`.
- `QRWATCH_SMTP_PORT`: SMTP port, defaulting to `465`.
- `QRWATCH_SMTP_USERNAME`: SMTP mailbox username, such as a QQ Mail address.
- `QRWATCH_SMTP_PASSWORD`: SMTP authorization code or app password, not a mailbox login password.
- `QRWATCH_SMTP_USE_SSL`: whether to use SMTP over SSL, defaulting to `true`.
- `QRWATCH_SMTP_TIMEOUT_SECONDS`: SMTP connection timeout, defaulting to `10`.
- `QRWATCH_NOTIFY_FROM`: optional sender address override; defaults to `QRWATCH_SMTP_USERNAME`.
- `QRWATCH_NOTIFY_TO`: notification recipient address.

QQ Mail SMTP local config example:

```dotenv
QRWATCH_NOTIFY_PROVIDER=qq-mail
QRWATCH_DRY_RUN=false
QRWATCH_SMTP_HOST=smtp.qq.com
QRWATCH_SMTP_PORT=465
QRWATCH_SMTP_USERNAME=your-address@qq.com
QRWATCH_SMTP_PASSWORD=your-local-authorization-code
QRWATCH_NOTIFY_TO=receiver@example.com
```

Planned provider-specific variables should follow this pattern:

- `QRWATCH_WEBHOOK_URL`: webhook-style provider endpoint, if added.

Secrets must not be printed in logs, preserved in artifacts, or included in screenshots.

## Reproducible Setup Command

Current safe validation command:

```bash
python tools/validate_harness_structure.py
```

Environment import smoke test:

```bash
conda run -n qrwatch python -c "import cv2, mss, PIL, numpy, dotenv, requests, pytest, pystray; print('python ok'); print(cv2.__version__)"
```

Application dry-run entrypoint:

```bash
conda run -n qrwatch python -m qrwatch
```

Application one-shot capture:

```bash
conda run -n qrwatch python -m qrwatch --once
```

Application background loop:

```bash
conda run -n qrwatch python -m qrwatch --run
```

Application tray process:

```bash
conda run -n qrwatch python -m qrwatch --tray
```

Packaged Windows executable build:

```powershell
.\tools\build_windows_executable.ps1
```

The tracked PyInstaller spec is `packaging/qrwatch.spec`; output is generated under ignored `build/` and `dist/` directories. See `docs/PACKAGING.md` for executable runtime behavior and validation.

Application test command:

```bash
conda run -n qrwatch python -m pytest
```
