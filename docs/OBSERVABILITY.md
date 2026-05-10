# Observability

Status: applied.

QR Watch should be easy to debug after it has been running in the background. Observability is local-first: logs, screenshots, and state live on the user's machine unless a human explicitly shares them.

## Product Logs

Location:

- Real runs: `%LOCALAPPDATA%\QRWatch\logs\`
- Harness/debug evidence: `artifacts/logs/qrwatch/` only when a task needs preserved evidence.

Format:

- Use JSON Lines (`.jsonl`) for machine-readable runtime logs.
- Include `timestamp`, `level`, `component`, `event`, `run_id`, and relevant safe fields.
- Include exception type and stack trace for errors.
- Redact secrets, provider tokens, webhook URLs, mailbox passwords, and raw QR payloads unless debug config explicitly allows payload logging.

Required component events:

- `app.starting`, `app.ready`, `app.paused`, `app.resumed`, `app.stopping`, `app.stopped`.
- `config.loaded`, `config.invalid`.
- `capture.started`, `capture.succeeded`, `capture.failed`.
- `screenshot.saved`, `screenshot.deleted`, `screenshot.save_failed`.
- `detector.started`, `detector.completed`, `detector.failed`.
- `dedup.accepted`, `dedup.suppressed`.
- `notifier.started`, `notifier.sent`, `notifier.dry_run`, `notifier.failed`.
- `tray.action`, `tray.error`.

Use `INFO` for lifecycle and normal cycle summaries, `DEBUG` for per-function call detail, `WARNING` for recoverable failures, and `ERROR` for failures that affect monitoring.

## Screenshot Evidence

Location:

- Real runs: `%LOCALAPPDATA%\QRWatch\screenshots\`
- Harness/debug evidence: `artifacts/screenshots/qrwatch/` only when explicitly preserved for a task.

Storage policy:

- Store screenshots because they are useful for debugging capture and detection.
- Do not keep them forever. Use retention by count and age.
- Default mode: keep recent screenshots, QR-positive screenshots, and error screenshots.
- Optional mode: store all screenshots for short debugging sessions only.

Suggested subdirectories:

- `recent\`: rolling buffer of normal screenshots.
- `detections\`: frames where one or more QR codes were detected.
- `errors\`: frames saved when capture, conversion, or detection fails after a frame exists.

Suggested filenames:

```text
YYYYMMDD-HHMMSS-ms_<cycle-id>_<kind>.png
```

Retention defaults:

- `recent`: keep last 200 screenshots or 24 hours, whichever is smaller.
- `detections`: keep 7 days by default.
- `errors`: keep 7 days by default.
- `all`: disabled by default; if enabled, warn in logs at startup.

Screenshots may contain private desktop content. Do not upload or commit them automatically.

## Runtime Counters

Maintain lightweight in-memory counters and write periodic summaries to logs:

- cycles started and completed.
- capture successes and failures.
- screenshots saved and deleted.
- QR-positive frames.
- QR codes detected.
- duplicate detections suppressed.
- notifications attempted, sent, dry-run logged, and failed.
- consecutive failures by component.

The tray status should use these counters to show a compact health summary.

## Traces

Location:

- Real runs: `%LOCALAPPDATA%\QRWatch\traces\` if trace files are enabled.
- Harness evidence: `artifacts/traces/qrwatch/` only when a task needs preserved evidence.

Trace format:

- One cycle trace may be a JSON object with `cycle_id`, timestamps, step durations, screenshot path, detection count, dedup result, notifier result, and final status.
- Enable trace files only during debugging or tests; normal logs should be enough for daily use.

## Review And Validation Evidence

- Review artifact location: `artifacts/reviews/`
- Validation artifact location: `artifacts/validation/`
- Current supervisor writes reviewer and validator outputs to `artifacts/runs/<run-id>/`.

Use standalone evidence directories only when evidence should be shared across runs or preserved separately from a single task run.

## Local Reproduction

Reproduce harness validation:

```bash
python tools/validate_harness_structure.py
```

Reproduce environment imports:

```bash
conda run -n qrwatch python -c "import cv2, mss, PIL, numpy, dotenv, requests, pytest, pystray; print('python ok'); print(cv2.__version__)"
```

Planned product reproduction commands:

```bash
conda run -n qrwatch python -m qrwatch --once --dry-run
conda run -n qrwatch python -m qrwatch --run --dry-run
conda run -n qrwatch python -m pytest
```

## Maintenance Artifacts

- Location: `artifacts/maintenance/`
- JSON report: `<timestamp>-entropy-control.json`
- Markdown report: `<timestamp>-entropy-control.md`
- Latest pointer: `latest-entropy-report.json`

Entropy reports preserve the findings that led to cleanup tasks, quality score updates, or human escalation.
