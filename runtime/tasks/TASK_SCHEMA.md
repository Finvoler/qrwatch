# Task Schema

Harness tasks are JSON files stored in `runtime/tasks/queue/`, `runtime/tasks/active/`, `runtime/tasks/completed/`, or `runtime/tasks/blocked/`.

Use JSON instead of YAML so the supervisor can parse tasks with the Python standard library.

Task filenames must match their `id`, for example `short-stable-id.json`. Task ids must use lowercase letters, numbers, and hyphens, with no leading or trailing hyphen.

## Required Fields

```json
{
  "id": "short-stable-id",
  "title": "Human-readable title",
  "status": "queued",
  "prompt": "The work request for the implementer agent.",
  "acceptance": ["Observable completion criterion"],
  "validation_commands": ["command to run when safe"]
}
```

## Optional Fields

```json
{
  "parent": "parent-task-id",
  "priority": 100,
  "created_at": "2026-04-29T00:00:00Z",
  "updated_at": "2026-04-29T00:00:00Z",
  "run_ids": [],
  "artifacts": [],
  "commit_policy": "never",
  "commit_type": "docs",
  "commit_message": "docs: update {task_id}",
  "notes": ""
}
```

`commit_policy` may be:

- `never`: do not commit this task automatically.
- `on_success`: commit after validator `passed` and reviewer `approved`.
- An object with `mode` plus optional `message` or `type`, for example `{"mode": "on_success", "type": "feat"}` or `{"mode": "on_success", "message": "feat: {title}"}`.

Commit message templates may use `{task_id}`, `{title}`, and `{run_id}`.

`commit_type` may be used when a task wants the supervisor to generate a standard message without supplying a full `commit_message`. Supported values are `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `style`, `build`, `ci`, `chore`, `deps`, `security`, `ops`, `eval`, `observability`, and `revert`. The default automatic commit message is `chore: complete {task_id}`.

## Status Values

- `queued`: ready for a supervisor loop to pick up.
- `active`: currently being worked by a run.
- `completed`: accepted or converted into follow-up tasks.
- `blocked`: requires human input or external action.

Task status must match its state directory. The only scaffold exception is `runtime/tasks/queue/example-task.json`, which may use `status: "example"` so it documents the schema without being picked up by the runner.

## Ralph Loop Semantics

One agent run does not need to finish all future work. It must either satisfy the current task, produce evidence that it is blocked, or create precise follow-up tasks. The next supervisor loop can then launch a fresh agent on the next queued task.
