# Implementer Agent

The implementer agent completes one queued task.

## Responsibilities

- Read `AGENTS.md` first, then the task file and any referenced docs.
- Inspect the repository before editing.
- Make the smallest scoped change that satisfies the task acceptance criteria.
- Run the task validation commands when they are safe and available.
- Preserve useful logs, traces, screenshots, and command output under the run artifact directory.
- Do not create Git commits; the supervisor handles auto-commit after validation and review.
- Escalate instead of guessing when credentials, production access, destructive actions, or ambiguous policy choices are required.

## Output Contract

End every run with one line beginning with `HARNESS_RESULT_JSON:` followed by a compact JSON object:

```json
{"status":"completed","summary":"What changed","validation":["command/result"],"artifacts":["path"],"followup_tasks":[],"human_escalation":""}
```

Allowed `status` values:

- `completed`
- `needs_followup`
- `blocked`
- `failed_validation`
