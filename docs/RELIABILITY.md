# Reliability

Status: applied.

QR Watch should keep running through ordinary desktop, detection, and network failures while making errors visible in the tray and logs. The first reliable version should favor simple behavior over hidden automation.

## Reliability Goals

- Keep the tray process responsive even when capture, detection, or notification fails.
- Avoid duplicate notification spam for the same QR payload.
- Preserve enough local evidence to debug failures.
- Recover automatically from transient capture and network errors.
- Escalate clearly when configuration or credentials are invalid.

## Failure Classes

- User input ambiguity: ask for clarification during development or mark the harness task blocked when a safe assumption is not possible.
- Configuration failure: missing required interval, invalid screenshot mode, invalid provider, or missing credentials for a real provider. Show error status and do not start monitoring.
- Capture failure: screenshot backend cannot access the desktop, monitor geometry changes, or frame conversion fails.
- Detection failure: OpenCV detector raises, image format is invalid, or QR decoding produces malformed output.
- Deduplication state failure: state file is missing, corrupt, locked, or not writable.
- Notification failure: provider credentials are invalid, network is unavailable, provider rejects the message, or timeout occurs.
- Storage failure: logs, screenshots, or state cannot be written.
- Policy or permission failure: stop and record human escalation for credentials, destructive operations, external sends, or unclear data-handling choices.

## Retry Policy

Capture:

- Retry on the next scheduled cycle.
- If 3 consecutive capture failures occur, mark status `degraded`.
- If 10 consecutive capture failures occur, mark status `error` and keep tray controls available.

Detection:

- Do not retry the same frame repeatedly in the hot loop.
- Log the failure and continue with the next scheduled screenshot.
- Save an error screenshot if a frame exists and screenshot storage is enabled.

Notification:

- Retry transient provider/network failures up to 3 attempts with short backoff.
- Do not retry invalid credentials or permanent provider rejection without user action.
- Queue failed notification events locally only if a real provider is enabled and the payload storage policy allows it.
- In dry-run mode, notification failures should be limited to logging/storage errors.

Storage:

- Retry once after creating missing directories.
- If screenshot storage fails, continue monitoring but mark status `degraded`.
- If logging fails, continue with console/tray-visible errors where possible.

Harness tools:

- Preserve command output in the run artifact and create follow-up work when retrying would hide the original failure.

## Deduplication Policy

Default deduplication window: 10 minutes.

Behavior:

- Normalize each QR payload before comparison.
- Hash payloads for state by default so raw QR contents do not need to be stored.
- Suppress repeated notifications for the same payload during the deduplication window.
- Log suppressed duplicates with safe metadata.
- Allow a future setting to notify again after expiry.

If a QR code appears in multiple screenshots within the window, keep detection evidence but send one notification.

## Screenshot Retention Policy

Screenshots are useful observability evidence but can be sensitive and large.

Defaults:

- Automatic screenshot retention is disabled unless
  `QRWATCH_SAVE_SCREENSHOTS=true`.
- When enabled, keep the last 200 screenshots or 24 hours by default.
- `QRWATCH_SCREENSHOT_MAX_COUNT` and `QRWATCH_SCREENSHOT_MAX_AGE_DAYS` control
  the limits.

Retention cleanup runs at startup and after retained screenshot saves. Cleanup
failure should log a warning but should not stop monitoring.

## State Recovery

- Store deduplication state under `%LOCALAPPDATA%\QRWatch\state\`.
- Write state atomically: write a temporary file, flush, then replace the previous state file.
- If state is corrupt, move it aside with a timestamp and start with empty state.
- Log state recovery events.

## Shutdown And Startup

Startup:

- Validate config before starting the worker loop.
- Create required local directories.
- Run screenshot retention cleanup.
- Start in paused or running mode according to config.

Shutdown:

- Stop accepting new tray actions.
- Let the current capture/detect/notify cycle finish or time out.
- Flush logs and deduplication state.
- Exit the tray icon cleanly.

## Rollback Policy

- Code changes: use Git review and normal patch reversal, never automatic destructive rollback.
- Runtime state: keep corrupt state backups rather than deleting them silently.
- Screenshots/logs: delete only through documented retention cleanup or explicit user action.
- External sends: cannot be rolled back; use dry-run mode and test recipients before enabling real providers.

## Required Evidence

Substantial runtime changes should preserve:

- Harness validation output.
- Environment import smoke output when dependencies change.
- Test output once product tests exist.
- Redacted log snippets for failures.
- Screenshot evidence only when needed and safe to preserve.

Notification-provider changes should also include:

- Dry-run event evidence.
- A statement of whether any external send was performed.
- Human approval evidence before real QQ, mailbox, WeChat, or webhook credentials are used.
