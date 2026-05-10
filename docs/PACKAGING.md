# Packaging

Status: applied.

QR Watch has a tracked PyInstaller build path for producing a local Windows executable from the `qrwatch` Conda environment.

## Entrypoint

The packaged executable uses:

```text
src/qrwatch/packaged.py
```

Default packaged behavior:

- Starts the tray UI when no explicit mode is supplied.
- Reads `%LOCALAPPDATA%\QRWatch\config.env` by default.
- Creates `%LOCALAPPDATA%\QRWatch\config.env` if it does not exist.
- Creates the starter config in dry-run mode with no credentials.
- Keeps runtime logs, deduplication state, and optional screenshots under `%LOCALAPPDATA%\QRWatch\` unless the config overrides them.

The packaged launcher still accepts normal CLI flags:

```powershell
.\dist\QRWatch\QRWatch.exe --config C:\path\to\config.env --tray
.\dist\QRWatch\QRWatch.exe --capture-once
.\dist\QRWatch\QRWatch.exe --run
```

`--config PATH` and `QRWATCH_CONFIG_FILE` point to explicit config files and must refer to existing files. The automatic starter-file behavior applies only to the default packaged config path.

## Build Command

From the repository root:

```powershell
.\tools\build_windows_executable.ps1
```

Equivalent direct command:

```powershell
conda run -n qrwatch pyinstaller --noconfirm --clean packaging\qrwatch.spec
```

The tracked PyInstaller spec is `packaging/qrwatch.spec`. Build output is generated under ignored `build/` and `dist/` folders. QR Watch uses PyInstaller's one-folder layout so startup does not depend on temporary one-file extraction. The expected executable path is:

```text
dist/QRWatch/QRWatch.exe
```

Do not commit files from `build/`, `dist/`, `%LOCALAPPDATA%\QRWatch\`, screenshots, QR payloads, or credential-bearing config files.

## Validation

Safe repository validation:

```powershell
python -m pytest
python tools\validate_harness_structure.py
```

Local executable validation after a build:

```powershell
.\dist\QRWatch\QRWatch.exe --capture-once
.\dist\QRWatch\QRWatch.exe --tray
```

One-shot capture may fail on machines where screenshot backends are unavailable or the session is not interactive. A successful tray launch should not require credentials because the starter config is dry-run by default.
