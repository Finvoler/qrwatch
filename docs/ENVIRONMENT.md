# Environment

QRWatch targets Windows and runs in the logged-in user session so it can access the interactive desktop for screenshots.

## Setup

```powershell
conda env create -f environment.yml
conda activate qrwatch
pip install -e .
```

The environment manifest installs Python 3.11 plus the runtime and test dependencies used by the project:

- `mss` for screenshot capture
- `opencv-python` for QR detection
- `pillow` and `numpy` for image handling
- `python-dotenv` for local config files
- `requests` for future webhook-style providers
- `pystray` for the tray process
- `pyinstaller` for Windows packaging
- `pytest` for tests

## Runtime Paths

By default, runtime files live under `%LOCALAPPDATA%\QRWatch`:

- `config.env`
- `dedup-state.json`
- `logs/`
- `screenshots/`

These locations can be overridden with the corresponding `QRWATCH_*` environment variables.

## Useful Commands

```powershell
python -m pytest
python -m qrwatch --capture-once
python -m qrwatch --run
python -m qrwatch --tray
```
