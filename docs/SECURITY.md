# Security

Status: applied.

QR Watch observes the user's desktop and may send messages through external providers. Treat screenshots, QR payloads, and notification credentials as sensitive by default.

## Secrets

- Storage: use local environment variables, repository-local `.env` files ignored by Git during development, or `%LOCALAPPDATA%\QRWatch\config.env` for real local runs.
- Files that must never contain secrets: tracked Markdown docs, `environment.yml`, source files, tests, benchmark definitions, run artifacts, and committed screenshots.
- Access: agents may document required secret names but must not request, infer, print, or commit real credentials.
- Rotation: if a credential is exposed, stop real sends, rotate the credential in the provider, and record a redacted incident note.
- Redaction: logs, traces, screenshots, and artifacts must redact provider tokens, webhook URLs, mailbox passwords, cookies, and raw QR payloads by default.

## Sensitive Data

- Screenshots may contain private desktop content.
- QR payloads may contain login links, tokens, payment data, or personal information.
- Notification destinations may reveal personal accounts.
- Provider configuration may include credentials and stable endpoint URLs.

Persistent state stores QR payload hashes by default, not raw payloads. Storing
raw QR payloads is a policy change that requires human approval.

## Permissions

- Default tool permissions: local repository reads, edits, validation commands, Conda environment checks, and artifact writes.
- Escalation process: stop the task and record a blocked result when credentials, real external sends, destructive actions, unclear policy choices, or production-like account access are required.
- Disallowed operations: automatic pushes, production writes, credential access without approval, destructive filesystem actions without approval, and unapproved external message sends.

## External Sends

- Dry-run notification is the default development behavior.
- Real QQ Mail-compatible SMTP sends require `QRWATCH_DRY_RUN=false`, human-provided SMTP credentials, and a test recipient.
- Real QQ bot, WeChat, or webhook sends remain future provider work and require human-provided credentials and a test target before implementation or validation.
- Tests must not contact external providers unless explicitly marked and approved for that run.
- Provider errors should be logged with redacted details.

## Screenshot Handling

- Real app screenshots live under `%LOCALAPPDATA%\QRWatch\screenshots\`.
- Automatic screenshot retention is disabled by default.
- When `QRWATCH_SAVE_SCREENSHOTS=true`, screenshot retention enforces
  `QRWATCH_SCREENSHOT_MAX_COUNT` and `QRWATCH_SCREENSHOT_MAX_AGE_DAYS`.
- Repository `artifacts/screenshots/` is only for explicit validation evidence.
- Do not upload, commit, or share screenshots automatically.
- Before preserving screenshot evidence in the repository, review or redact sensitive content.

## Git Automation

The harness loop may create local commits only when auto-commit is explicitly enabled and the worktree is clean before the run starts. The loop must not push, merge, tag, or rewrite history without human approval.

## Human Escalation

Require human approval for:

- credentials or provider account setup.
- real notification sends.
- storing raw QR payloads.
- committing screenshots or logs that may contain private data.
- destructive operations.
- unclear security or privacy decisions.
