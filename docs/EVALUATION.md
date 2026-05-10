# Evaluation

Status: applied.

The evaluation loop combines existing harness smoke checks with QR Watch product checks. Product checks start lightweight because source code does not exist yet; they should become runnable benchmarks as milestones land.

## Required Checks Now

Run harness validation after documentation, task, guardrail, or framework layout changes:

```bash
python tools/validate_harness_structure.py
```

Run the environment import smoke test after dependency changes:

```bash
conda run -n qrwatch python -c "import cv2, mss, PIL, numpy, dotenv, requests, pytest, pystray; print('python ok'); print(cv2.__version__)"
```

Run the generic harness smoke suite before large harness changes:

```bash
python tools/run_evals.py --suite smoke
```

## Product Checks To Add

Once `src/qrwatch/` exists, add product tests for:

- config loading and validation.
- screenshot storage path creation and retention cleanup.
- QR-positive and QR-negative fixture detection.
- QR payload normalization and hashing.
- deduplication window behavior.
- dry-run notifier behavior.
- notifier failure classification.
- tray controller state transitions without calling real capture or notifier code from UI handlers.

Expected product test command:

```bash
conda run -n qrwatch python -m pytest
```

## Product Smoke Eval Plan

Create a product smoke suite after the package skeleton exists. Initial benchmark candidates:

- `qrwatch-config-smoke`: validates default config, `.env` loading, and invalid config failures.
- `qrwatch-detector-fixtures`: runs QR detection against one positive and one negative fixture.
- `qrwatch-dedup-smoke`: verifies repeated payload suppression and expiry.
- `qrwatch-dry-run-notifier`: verifies notification events are logged without external sends.
- `qrwatch-retention-smoke`: verifies screenshot retention cleanup on a temporary directory.

The first product eval suite should avoid real screenshots and external sends. Use fixtures and temporary directories so it can run in CI or local headless contexts.

## Manual Windows Checks

Some behavior requires a logged-in Windows desktop session and should remain manual until stable automation exists:

- tray icon appears and menu actions work.
- `--once --dry-run` can capture the current desktop.
- screenshot files appear under `%LOCALAPPDATA%\QRWatch\screenshots\`.
- pause and resume stop and restart the worker loop.
- exit flushes logs and state.

Manual checks should record redacted notes in validation evidence only when they explain a decision or regression.

## Runner

Use the smoke suite before merging harness changes:

```bash
python tools/run_evals.py --suite smoke
```

List available benchmarks:

```bash
python tools/run_evals.py --list
```

The runner writes result JSON files into `evals/results/`. These files are ignored by default because they are machine-specific; force-add one only when it explains an important decision or regression.

By default, the runner compares the selected suite against a versioned baseline in `evals/baselines/<suite>.json`. Update the baseline only after a known-good run:

```bash
python tools/run_evals.py --suite smoke --update-baseline
```

Skip baseline comparison for exploratory local checks:

```bash
python tools/run_evals.py --suite smoke --no-baseline
```

## Results

Store eval outputs in `evals/results/`.

Each result should record:

- task id or benchmark id.
- commit or version.
- model or agent configuration when applicable.
- cost when available.
- latency.
- pass or fail status.
- notes and artifacts.

Harness-loop runs should reference `artifacts/runs/<run-id>/summary.json`.

## Regression Policy

The eval runner exits nonzero when any selected benchmark fails or when the current result regresses from the tracked baseline. This makes regressions visible before merge in local checks or CI.

The smoke suite intentionally uses preview mode so it does not require Codex availability, credentials, network access, or permission prompts. Product-specific suites should keep the same property until real external integration tests are explicitly approved.
