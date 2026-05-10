# Time Conventions

QRWatch uses local time for user-facing output and UTC for internal deduplication state.

## Local Time

Use local time for:

- log timestamps
- CLI capture timestamps
- notification text shown to users
- retained screenshot filenames

## UTC

Use UTC for persisted deduplication timestamps in the JSON state file so duplicate suppression remains stable across time zone changes.
