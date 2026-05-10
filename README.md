# QRWatch

QRWatch is a local Windows QR detection watcher. It can capture the desktop, detect QR codes, suppress repeated notifications, and send alerts through a notifier provider.

Current modes:

- one-shot run without background loop
- one-shot screen capture and QR detection
- continuous background watcher
- Windows tray process
- dry-run notifications or QQ Mail-compatible SMTP email

## Quick Start

```powershell
conda env create -f environment.yml
conda activate qrwatch
pip install -e .
python -m pytest
python -m qrwatch --capture-once
```

## Configuration

The app reads environment variables or a dotenv-style config file. Use [.env.example](.env.example) as a starting point, or let the packaged app create `%LOCALAPPDATA%\QRWatch\config.env` on first launch.

Common settings:

- `QRWATCH_NOTIFY_PROVIDER=dry-run` keeps notifications local.
- `QRWATCH_DRY_RUN=true` avoids real sends until credentials are ready.
- `QRWATCH_MONITOR_INDEX=1` captures the primary monitor.
- `QRWATCH_DEDUP_WINDOW_SECONDS=300` suppresses repeated notifications for five minutes.

## Common Commands

```powershell
python -m qrwatch --capture-once
python -m qrwatch --run
python -m qrwatch --tray
python -m pytest
```

## Packaging

Build a Windows executable with:

```powershell
.\tools\build_windows_executable.ps1
```

See [docs/PACKAGING.md](docs/PACKAGING.md) for packaged runtime behavior and output paths.
