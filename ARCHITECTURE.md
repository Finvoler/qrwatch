# Architecture

Status: applied first pass.

This repository is a Codex harness for a planned Windows Python app. The app will run in the background, periodically capture screenshots from the logged-in Windows desktop, detect QR codes in those screenshots, and notify a configured channel through a provider interface.

The first application source skeleton exists under `src/qrwatch/`. It currently supports configuration loading, a dry-run entrypoint, mss-backed capture-once screen inspection, OpenCV-backed QR detection, JSON-backed deduplication events, dry-run or QQ Mail-compatible SMTP notification dispatch, a continuous background controller, a pystray-based user-session tray process, and a PyInstaller packaged launcher.

## Product Shape

The first app should be a small local agent with these responsibilities:

- Capture the screen on a configurable interval.
- Decode one or more QR codes from each captured frame.
- Deduplicate detections so the same QR code does not spam notifications.
- Send detection events through a notifier interface.
- Persist enough local state and logs to debug failures without storing sensitive screenshots by default.

The first implementation should run inside the logged-in user session. A Windows service can be explored later, but desktop screenshot access from a service has extra Windows session and permission constraints.

## Product Layers

Intended source layout:

- `src/qrwatch/app.py`: application composition and lifecycle.
- `src/qrwatch/background.py`: continuous worker loop and lifecycle controls.
- `src/qrwatch/config.py`: environment and config-file loading.
- `src/qrwatch/capture.py`: Windows screenshot capture abstraction.
- `src/qrwatch/detectors/`: QR detection implementation.
- `src/qrwatch/events.py`: QR detection event shaping.
- `src/qrwatch/notifiers/`: notifier interface plus dry-run and QQ Mail-compatible SMTP email adapters; QQ, WeChat, and webhook adapters remain future extension points.
- `src/qrwatch/state.py`: deduplication state and local persistence.
- `src/qrwatch/storage.py`: local screenshot retention paths and pruning.
- `src/qrwatch/logging.py`: log configuration and redaction helpers.
- `src/qrwatch/tray.py`: Windows system tray entrypoint and folder actions.
- `src/qrwatch/packaged.py`: Windows executable entrypoint that defaults to tray mode and local editable config.
- `tests/`: unit tests and small image fixtures.

This layout was confirmed when the milestone-2 package skeleton was added. Capture, detector, event shaping, and state modules now contain first implementations; notifier modules still contain placeholders until their implementation milestone.

## Dependency Boundaries

Allowed dependency direction:

- `app` may depend on `config`, `capture`, `detectors`, `notifiers`, `state`, and `logging`.
- `capture` should only return image/frame data and metadata. It should not know about QR decoding or notification providers.
- `detectors` should accept image/frame data and return structured QR detection results.
- `notifiers` should accept structured detection events. They should not capture screenshots or decode QR codes.
- `state` should handle deduplication and local persistence only.

Forbidden dependencies:

- Detection code must not send messages directly.
- Notification adapters must not read screenshots from disk unless a future provider explicitly requires attachments and the user approves that behavior.
- Harness tools under `tools/` must not import app runtime modules unless a specific validation command is added for that purpose.

Generated files:

- Current package/runtime commands generate local logs, deduplication state, and
  optional retained screenshots under `%LOCALAPPDATA%\QRWatch\` by default.
- PyInstaller output is generated only by the local packaging command and stays
  under ignored `dist/` and `build/` folders.

Contract files:

- `runtime/tasks/TASK_SCHEMA.md` is the harness task contract.
- App config is loaded from optional dotenv-style config files and `QRWATCH_*` environment variables in `src/qrwatch/config.py`. Packaged runs default to `%LOCALAPPDATA%\QRWatch\config.env` and create a dry-run starter config if it is missing.
- The implemented real notifier is SMTP email. `qq-mail`, `qqmail`, and `email` map to the same SMTP adapter.

## Runtime Core

The harness runtime provides:

- Task intake and normalization through `runtime/tasks/queue/*.json`.
- Tool execution with explicit permissions.
- File-based state persistence for task progress, decisions, and artifacts.
- Stop conditions, retry rules, and failure classification.
- Isolated local runs, tests, and validation commands.

The product runtime is separate from the harness runtime. The product app will own the screenshot loop, QR detection, notification dispatch, and app logs.

## Extension Points

Harness extension points:

- Tool adapters.
- Repository knowledge indexers.
- Evaluation runners.
- Observability collectors.
- Policy and guardrail checks.
- Reviewer or maintenance agents.

Product extension points:

- Screenshot backend.
- QR detector backend.
- Notification provider adapters.
- Deduplication strategy.
- Packaging and background-run strategy.

## State Model

Harness records:

- Task request: `runtime/tasks/queue/*.json`.
- Plan and progress: `docs/exec-plans/active/`, task status directories under `runtime/tasks/`, and `artifacts/runs/<run-id>/summary.json`.
- Tool calls and outputs: role outputs under `artifacts/runs/<run-id>/`.
- Artifacts: `artifacts/`.
- Eval results: `evals/results/`.
- Human approvals and escalation history: task status, role JSON output, and preserved run artifacts.

Product records:

- App config: optional dotenv-style local config file plus `QRWATCH_*` environment variables. Environment variables override file values.
- Deduplication state: JSON store at the configured state path, defaulting to `%LOCALAPPDATA%\QRWatch\dedup-state.json`.
- QR payload persistence: deduplication state stores SHA-256 payload hashes and timestamps, not raw QR payloads.
- Logs: rotating text log at `%LOCALAPPDATA%\QRWatch\logs\qrwatch.log` by default.
- Screenshots: automatic retention is disabled by default. If enabled, retained PNG files live under `%LOCALAPPDATA%\QRWatch\screenshots\` and are pruned by count and age.

## Isolation Model

- Worktrees or task branches: current scaffold runs in the active repository. Future task branches are optional.
- Local services and ports: no local service or port is required for the first prototype.
- Credentials and secrets: notification credentials must be supplied by a human and excluded from Git.
- Runtime artifacts: harness artifacts are stored under `artifacts/`.
- Production or external systems: notification providers are external systems. Sending real messages requires human-supplied credentials, `QRWATCH_DRY_RUN=false`, and a test recipient.

## Security And Privacy Rules

- Treat screenshots as sensitive because they may contain private desktop content.
- Do not preserve screenshots in repository `artifacts/` unless the task explicitly needs evidence and sensitive content has been reviewed or redacted.
- Never commit notification credentials, QR payload secrets, mailbox tokens, webhook URLs, or provider cookies.
- Use test recipients and dry-run notifiers before enabling real QQ, mailbox, WeChat, or webhook sends.
- Escalate to a human before connecting a real messaging account, storing raw QR payloads, or committing persistent screenshots.

## Validation Matrix

Current harness validation:

```bash
python tools/validate_harness_structure.py
```

Current environment validation:

```bash
conda run -n qrwatch python -c "import cv2, mss, PIL, numpy, dotenv, requests, pytest; print('python ok'); print(cv2.__version__)"
```

Planned app validation:

- Unit tests for config loading, deduplication, QR event shaping, and notifier interface behavior.
- Fixture-based QR detection tests using static test images.
- Dry-run notification tests that do not contact external services.
- QQ Mail-compatible SMTP notification tests use fake SMTP clients and do not contact external services.
- Optional Windows manual validation for background capture behavior.

Primary test command:

```bash
conda run -n qrwatch python -m pytest
```

Dry-run module entrypoint:

```bash
conda run -n qrwatch python -m qrwatch
```

Continuous background loop:

```bash
conda run -n qrwatch python -m qrwatch --run
```

Tray process:

```bash
conda run -n qrwatch python -m qrwatch --tray
```

## Open Decisions

- Packaging model: scheduled task, PyInstaller executable, or installer.
- Webhook, WeChat, and QQ bot notification providers beyond QQ Mail SMTP.
- Long-term QR payload retention after notification; current deduplication state stores only hashes.
- App name. This document uses `qrwatch` as a working name.
