from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = ROOT / "runtime" / "tasks"

TASK_STATE_DIRS = {
    "queue": "queued",
    "active": "active",
    "completed": "completed",
    "blocked": "blocked",
}

TASK_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")
EXAMPLE_TASK = TASK_ROOT / "queue" / "example-task.json"
ALLOWED_COMMIT_TYPES = {
    "feat",
    "fix",
    "docs",
    "test",
    "refactor",
    "perf",
    "style",
    "build",
    "ci",
    "chore",
    "deps",
    "security",
    "ops",
    "eval",
    "observability",
    "revert",
}
COMMIT_MESSAGE_PATTERN = re.compile(
    rf"^({'|'.join(sorted(ALLOWED_COMMIT_TYPES))})(\([a-z0-9._-]+\))?: .+"
)


def fail(message: str, remediation: str) -> str:
    return f"{message} Fix: {remediation}"


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(is_non_empty_string(item) for item in value)


def has_valid_commit_message_prefix(value: str) -> bool:
    return bool(COMMIT_MESSAGE_PATTERN.fullmatch(value.strip()))


def validate_task_file(path: Path) -> list[str]:
    failures: list[str] = []
    task_path = relative(path)

    try:
        task = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [
            fail(
                f"{task_path} is not valid JSON: {exc}",
                "Repair the JSON syntax or remove the invalid task file.",
            )
        ]

    if not isinstance(task, dict):
        return [
            fail(
                f"{task_path} must contain a JSON object.",
                "Replace the file contents with one task object.",
            )
        ]

    required_string_fields = ("id", "title", "status", "prompt")
    for field in required_string_fields:
        if not is_non_empty_string(task.get(field)):
            failures.append(
                fail(
                    f"{task_path} field `{field}` must be a non-empty string.",
                    f"Add a meaningful `{field}` value.",
                )
            )

    task_id = task.get("id")
    if isinstance(task_id, str):
        if not TASK_ID_PATTERN.fullmatch(task_id):
            failures.append(
                fail(
                    f"{task_path} id `{task_id}` is not a stable lowercase task id.",
                    "Use lowercase letters, numbers, and hyphens; keep it 1-64 characters with no edge hyphen.",
                )
            )
        expected_name = f"{task_id}.json"
        if path.name != expected_name:
            failures.append(
                fail(
                    f"{task_path} filename does not match task id `{task_id}`.",
                    f"Rename the file to `{expected_name}` or update the id.",
                )
            )

    if not is_string_list(task.get("acceptance")):
        failures.append(
            fail(
                f"{task_path} field `acceptance` must be a non-empty string list.",
                "Add one or more observable acceptance criteria.",
            )
        )

    if not is_string_list(task.get("validation_commands")):
        failures.append(
            fail(
                f"{task_path} field `validation_commands` must be a non-empty string list.",
                "Add safe local validation commands, such as `python tools/validate_harness_structure.py`.",
            )
        )

    parent_dir = path.parent.name
    expected_status = TASK_STATE_DIRS.get(parent_dir)
    status = task.get("status")
    if path == EXAMPLE_TASK and status == "example":
        expected_status = "example"

    if expected_status is None:
        failures.append(
            fail(
                f"{task_path} is outside the task state directories.",
                "Move task JSON files under runtime/tasks/queue, active, completed, or blocked.",
            )
        )
    elif status != expected_status:
        failures.append(
            fail(
                f"{task_path} status `{status}` does not match directory `{parent_dir}`.",
                f"Set status to `{expected_status}` or move the task to the matching directory.",
            )
        )

    optional_string_fields = ("parent", "created_at", "updated_at", "commit_type", "commit_message", "notes")
    for field in optional_string_fields:
        value = task.get(field)
        if value is not None and not isinstance(value, str):
            failures.append(
                fail(
                    f"{task_path} optional field `{field}` must be a string when present.",
                    f"Change `{field}` to a string or remove it.",
                )
            )

    commit_type = task.get("commit_type")
    if isinstance(commit_type, str) and commit_type not in ALLOWED_COMMIT_TYPES:
        failures.append(
            fail(
                f"{task_path} commit_type `{commit_type}` is not supported.",
                f"Use one of: {', '.join(sorted(ALLOWED_COMMIT_TYPES))}.",
            )
        )

    commit_message = task.get("commit_message")
    if isinstance(commit_message, str) and commit_message.strip() and not has_valid_commit_message_prefix(commit_message):
        failures.append(
            fail(
                f"{task_path} commit_message must start with a supported functional prefix.",
                "Use a format such as `docs: update task schema` or `feat(runtime): add commit metadata`.",
            )
        )

    if "priority" in task and not isinstance(task["priority"], int):
        failures.append(
            fail(
                f"{task_path} optional field `priority` must be an integer.",
                "Use an integer priority, where lower numbers run first.",
            )
        )

    for field in ("run_ids", "artifacts"):
        if field in task and not isinstance(task[field], list):
            failures.append(
                fail(
                    f"{task_path} optional field `{field}` must be a list.",
                    f"Use an array for `{field}`.",
                )
            )
        elif field in task and not all(isinstance(item, str) for item in task[field]):
            failures.append(
                fail(
                    f"{task_path} optional field `{field}` must only contain strings.",
                    f"Store relative path or id strings in `{field}`.",
                )
            )

    commit_policy = task.get("commit_policy")
    if commit_policy is not None:
        valid_modes = {"never", "on_success"}
        if isinstance(commit_policy, str):
            if commit_policy not in valid_modes:
                failures.append(
                    fail(
                        f"{task_path} commit_policy `{commit_policy}` is not supported.",
                        "Use `never`, `on_success`, or an object with a valid `mode`.",
                    )
                )
        elif isinstance(commit_policy, dict):
            mode = commit_policy.get("mode")
            message = commit_policy.get("message")
            policy_type = commit_policy.get("type")
            if mode not in valid_modes:
                failures.append(
                    fail(
                        f"{task_path} commit_policy object must include mode `never` or `on_success`.",
                        "Set `commit_policy.mode` to a supported mode.",
                    )
                )
            if message is not None and not isinstance(message, str):
                failures.append(
                    fail(
                        f"{task_path} commit_policy.message must be a string when present.",
                        "Use a string commit message template or remove the field.",
                    )
                )
            elif isinstance(message, str) and message.strip() and not has_valid_commit_message_prefix(message):
                failures.append(
                    fail(
                        f"{task_path} commit_policy.message must start with a supported functional prefix.",
                        "Use a format such as `fix: handle blocked task state` or `test(evals): add smoke baseline`.",
                    )
                )
            if policy_type is not None and policy_type not in ALLOWED_COMMIT_TYPES:
                failures.append(
                    fail(
                        f"{task_path} commit_policy.type `{policy_type}` is not supported.",
                        f"Use one of: {', '.join(sorted(ALLOWED_COMMIT_TYPES))}.",
                    )
                )
        else:
            failures.append(
                fail(
                    f"{task_path} commit_policy must be a string or object.",
                    "Use `never`, `on_success`, or an object with `mode` and optional `message`.",
                )
            )

    return failures


def collect_failures() -> list[str]:
    failures: list[str] = []

    if not TASK_ROOT.exists():
        return [
            fail(
                "runtime/tasks is missing.",
                "Create runtime/tasks with queue, active, completed, and blocked directories.",
            )
        ]

    for path in sorted(TASK_ROOT.rglob("*.json")):
        if path.parent.name not in TASK_STATE_DIRS:
            failures.append(
                fail(
                    f"{relative(path)} is not inside a task state directory.",
                    "Move task JSON files under runtime/tasks/queue, active, completed, or blocked.",
                )
            )
            continue
        failures.extend(validate_task_file(path))

    return failures


def main() -> int:
    failures = collect_failures()

    if failures:
        print("Harness guardrail validation failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("Harness guardrail validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
