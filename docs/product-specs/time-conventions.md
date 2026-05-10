# Time Conventions

Status: implemented.

QR Watch uses two time conventions because user-facing runtime evidence and
internal deduplication state have different needs.

## User-Facing Time

Use the system local time zone for timestamps that a person reads directly:

- log timestamps emitted by Python logging.
- captured frame metadata shown by the CLI.
- notification text such as `Detected at`.
- retained screenshot filenames.

This makes local troubleshooting match the Windows clock and the user's tray
session.

## Internal State Time

Use UTC for persisted deduplication timestamps in the JSON state file.

This keeps duplicate suppression stable if the system time zone changes, and it
avoids ambiguous comparisons around daylight-saving transitions. Raw QR payloads
are not stored in this state; only payload hashes and timestamps are persisted.

