# Guardrails

Status: applied.

Guardrails define rules that should become mechanical checks where practical. For QR Watch, the highest-risk areas are screenshots, QR payloads, notification credentials, and external message sends.

## Structural Rules

- Required files and directories are checked by `tools/validate_harness_structure.py`.
- Task JSON schema, status-directory alignment, task id naming, and filename/id matching are checked by `tools/validate_guardrails.py`.
- Entropy control findings are checked by `tools/entropy_control.py`.
- The outer loop task state must live under `runtime/tasks/`.
- Role definitions must live under `docs/agent-roles/`.
- Run evidence must live under `artifacts/runs/`.
- Maintenance evidence must live under `artifacts/maintenance/`.
- `AGENTS.md` must stay under the validator size limit.

## Product Dependency Guardrails

Expected source layers are documented in `ARCHITECTURE.md`.

Allowed dependencies:

- `app` may compose all product layers.
- `capture` may depend on screenshot and image libraries.
- `detectors` may depend on image and QR detection libraries.
- `notifiers` may depend on provider clients, `requests`, and standard mail libraries.
- `state` may depend on local filesystem, JSON, SQLite, hashing, and time utilities.

Forbidden dependencies:

- `detectors` must not send notifications.
- `capture` must not decode QR codes or call notifiers.
- `notifiers` must not capture screenshots.
- `tools/` should not import product runtime modules unless a specific validation command requires it.

Mechanical check: planned after `src/qrwatch/` exists. First implementation can be a small import-boundary check in `tools/validate_qrwatch_boundaries.py`.

## Product Safety Guardrails

- Do not commit notification credentials, mailbox passwords, QQ credentials, WeChat credentials, webhook URLs, provider cookies, or `.env` files.
- Do not perform real external sends unless the user explicitly provides credentials and a test recipient for that run.
- Default notifier mode must be dry-run until a real provider is configured.
- QR payloads should be hashed or redacted in persistent state and logs by default.
- Screenshots may be stored locally under `%LOCALAPPDATA%\QRWatch\screenshots\` with retention, but must not be committed.
- Repository `artifacts/screenshots/` may contain screenshots only when a task explicitly requires evidence and the user has reviewed or approved the content.
- Logs must redact secrets, tokens, webhook URLs, and raw QR payloads unless a debug setting explicitly allows payload logging.
- Generated packaging output must be documented before agents edit or delete it.

Mechanical checks available now:

- `.gitignore` ignores `.env`, logs, runtime databases, and harness artifact contents by default.
- `python tools/validate_harness_structure.py` validates harness paths and task guardrails.

Planned checks:

- Secret-pattern scanner for `.env`, webhook URLs, SMTP passwords, and common token names.
- Screenshot artifact scanner that warns when image files are staged under repository artifacts.
- QR payload logging test once logging code exists.
- Dry-run default test once notifier code exists.

## Changed-File Requirements

- `AGENTS.md`, `ARCHITECTURE.md`, `PLANS.md`, or `docs/*.md`: run `python tools/validate_harness_structure.py`.
- `environment.yml`: run the Conda import smoke test from `docs/ENVIRONMENT.md`.
- `tools/*.py`: run `python tools/validate_harness_structure.py` and the relevant tool command.
- Future `src/qrwatch/capture.py`: run screenshot capture smoke tests and avoid preserving screenshots unless needed.
- Future `src/qrwatch/detectors/`: run QR fixture tests.
- Future `src/qrwatch/notifiers/`: run dry-run notifier tests; real sends require human approval.
- Future `src/qrwatch/state.py`: run deduplication and state-recovery tests.
- Future tray UI code: run unit tests plus a manual tray smoke check on Windows.

## Tool Rules

- Allowed tools: repository-local reads, edits, local validation commands, Conda environment checks, and artifact writes.
- Conditionally allowed tools: local `git add --all .` and `git commit` after a successful harness loop run when auto-commit is explicitly enabled.
- Restricted tools: production changes, credential access, destructive filesystem operations, external service mutation, automatic pushes, automatic merges.
- Escalation-required tools: anything outside the local harness permission model or requiring secrets.

## Git Commit Guardrails

- Auto-commit requires a clean worktree before the task starts.
- Auto-commit must run after validation and review, not before.
- Auto-commit must not include remote mutation such as `git push`.
- Auto-commit failures should leave evidence in the run output and require human follow-up.

## Documentation Rules

- `AGENTS.md` must remain concise.
- Durable knowledge belongs in focused docs.
- Active execution plans belong in `docs/exec-plans/active/`.
- Role-specific behavior belongs in `docs/agent-roles/`, not in `AGENTS.md`.
- Machine-readable task state belongs in JSON files under `runtime/tasks/`.
- Product roadmap belongs in `PLANS.md`.

## Future Checks

- `tools/validate_qrwatch_boundaries.py`: planned dependency boundary check.
- `tools/validate_qrwatch_security.py`: planned secret, screenshot artifact, and unsafe notifier config check.
- Product smoke eval suite: planned after the package skeleton exists.
- Stale documentation checker: available through `tools/entropy_control.py`.
- Eval regression gate: available through `tools/run_evals.py`.
