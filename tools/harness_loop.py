from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TASK_ROOT = ROOT / "runtime" / "tasks"
QUEUE_DIR = TASK_ROOT / "queue"
ACTIVE_DIR = TASK_ROOT / "active"
COMPLETED_DIR = TASK_ROOT / "completed"
BLOCKED_DIR = TASK_ROOT / "blocked"
RUNS_DIR = ROOT / "artifacts" / "runs"
ROLE_DIR = ROOT / "docs" / "agent-roles"

RESULT_MARKER = "HARNESS_RESULT_JSON:"
CODEX_COMMAND = "codex"
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


@dataclass
class StageResult:
    role: str
    status: str
    summary: str
    output_path: Path
    parsed: dict[str, Any]


@dataclass
class CommitResult:
    status: str
    summary: str
    commit_sha: str = ""
    output: str = ""


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def update_task_status(task: dict[str, Any], status: str, run_id: str, artifacts: list[str]) -> None:
    task["status"] = status
    task["updated_at"] = datetime.now(timezone.utc).isoformat()
    task.setdefault("run_ids", [])
    if run_id not in task["run_ids"]:
        task["run_ids"].append(run_id)
    task.setdefault("artifacts", [])
    for artifact in artifacts:
        if artifact not in task["artifacts"]:
            task["artifacts"].append(artifact)


def next_task() -> Path | None:
    candidates = sorted(
        QUEUE_DIR.glob("*.json"),
        key=lambda path: (
            int(load_json(path).get("priority", 100)),
            path.name,
        ),
    )
    for path in candidates:
        task = load_json(path)
        if task.get("status") == "queued":
            return path
    return None


def role_text(role: str) -> str:
    path = ROLE_DIR / f"{role}.md"
    if not path.exists():
        raise FileNotFoundError(f"missing role file: {path}")
    return path.read_text(encoding="utf-8")


def build_prompt(
    *,
    role: str,
    task_path: Path,
    task: dict[str, Any],
    run_dir: Path,
    previous_artifacts: list[Path],
) -> str:
    role_doc = role_text(role)
    artifact_list = "\n".join(f"- {path.relative_to(ROOT)}" for path in previous_artifacts) or "- None"
    validation_commands = "\n".join(f"- {cmd}" for cmd in task.get("validation_commands", [])) or "- None"
    acceptance = "\n".join(f"- {item}" for item in task.get("acceptance", [])) or "- None"

    return f"""You are the {role} agent for this harness run.

Read and obey AGENTS.md first. Then use this role definition:

```md
{role_doc}
```

Task file: {task_path.relative_to(ROOT)}
Run artifact directory: {run_dir.relative_to(ROOT)}

Task:
```json
{json.dumps(task, indent=2, ensure_ascii=True)}
```

Acceptance criteria:
{acceptance}

Validation commands:
{validation_commands}

Previous artifacts:
{artifact_list}

Write any role-specific artifact into the run artifact directory unless the role definition or this prompt names a more specific path.

At the end, print exactly one final line starting with:
{RESULT_MARKER}

The text after the marker must be valid compact JSON matching the role output contract.
"""


def run_codex(
    *,
    invocation_prompt: str,
    output_path: Path,
    execute: bool,
) -> tuple[int, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if not execute:
        text = "Preview only; Codex was not invoked.\n"
        output_path.write_text(text, encoding="utf-8")
        return 0, text

    resolved_codex = shutil.which(CODEX_COMMAND)
    if resolved_codex is None:
        text = f"Codex command not found in PATH: {CODEX_COMMAND}\n"
        output_path.write_text(text, encoding="utf-8")
        return 127, text

    command = [resolved_codex, "exec", "--full-auto", "-C", str(ROOT), invocation_prompt]

    try:
        completed = subprocess.run(
            command,
            cwd=str(ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        text = f"Failed to launch Codex command: {resolved_codex}\n{exc}\n"
        output_path.write_text(text, encoding="utf-8", errors="replace")
        return 127, text
    text = (
        "STDOUT:\n"
        + (completed.stdout or "")
        + "\nSTDERR:\n"
        + (completed.stderr or "")
        + f"\nRETURN_CODE: {completed.returncode}\n"
    )
    output_path.write_text(text, encoding="utf-8", errors="replace")
    return completed.returncode, text


def parse_result(role: str, output_path: Path, text: str, return_code: int, execute: bool) -> StageResult:
    if not execute:
        return StageResult(
            role=role,
            status="preview",
            summary="Preview only; Codex was not invoked.",
            output_path=output_path,
            parsed={},
        )

    matches = re.findall(rf"{re.escape(RESULT_MARKER)}\s*(\{{.*\}})", text)
    if not matches:
        status = "blocked" if return_code != 0 else "needs_followup"
        return StageResult(
            role=role,
            status=status,
            summary=f"No {RESULT_MARKER} line found.",
            output_path=output_path,
            parsed={"status": status},
        )

    try:
        parsed = json.loads(matches[-1])
    except json.JSONDecodeError as exc:
        return StageResult(
            role=role,
            status="blocked",
            summary=f"Invalid result JSON: {exc}",
            output_path=output_path,
            parsed={"status": "blocked"},
        )

    return StageResult(
        role=role,
        status=str(parsed.get("status", "unknown")),
        summary=str(parsed.get("summary", "")),
        output_path=output_path,
        parsed=parsed,
    )


def run_stage(
    *,
    role: str,
    task_path: Path,
    task: dict[str, Any],
    run_dir: Path,
    previous_artifacts: list[Path],
    execute: bool,
) -> StageResult:
    prompt = build_prompt(
        role=role,
        task_path=task_path,
        task=task,
        run_dir=run_dir,
        previous_artifacts=previous_artifacts,
    )
    prompt_path = run_dir / f"{role}.prompt.md"
    prompt_path.write_text(prompt, encoding="utf-8")
    output_path = run_dir / f"{role}.txt"
    invocation_prompt = (
        f"Read and execute the harness prompt at {prompt_path.relative_to(ROOT)}. "
        f"End with the required {RESULT_MARKER} line."
    )
    return_code, text = run_codex(
        invocation_prompt=invocation_prompt,
        output_path=output_path,
        execute=execute,
    )
    return parse_result(role, output_path, text, return_code, execute)


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug[:60] or "followup"


def write_followup_tasks(parent_task: dict[str, Any], planner_result: StageResult) -> list[Path]:
    created: list[Path] = []
    parent_id = str(parent_task["id"])
    followups = planner_result.parsed.get("followup_tasks", [])
    if not isinstance(followups, list):
        return created

    for index, item in enumerate(followups, start=1):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", f"Follow-up {index}")).strip()
        task_id = f"{parent_id}-f{index:02d}-{slugify(title)}"
        task = {
            "id": task_id,
            "title": title,
            "status": "queued",
            "parent": parent_id,
            "priority": int(parent_task.get("priority", 100)) + index,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "prompt": str(item.get("prompt", title)).strip(),
            "acceptance": item.get("acceptance", []),
            "validation_commands": item.get("validation_commands", parent_task.get("validation_commands", [])),
            "run_ids": [],
            "artifacts": [str(planner_result.output_path.relative_to(ROOT))],
            "notes": f"Generated from parent task {parent_id}.",
        }
        path = QUEUE_DIR / f"{task_id}.json"
        suffix = 2
        while path.exists():
            path = QUEUE_DIR / f"{task_id}-{suffix}.json"
            suffix += 1
        write_json(path, task)
        created.append(path)
    return created


def move_task(task_path: Path, destination_dir: Path, task: dict[str, Any]) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / task_path.name
    write_json(destination, task)
    if task_path.resolve() != destination.resolve() and task_path.exists():
        task_path.unlink()
    return destination


def run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
    )


def commit_mode(task: dict[str, Any], auto_commit: bool) -> str:
    policy = task.get("commit_policy")
    if isinstance(policy, dict):
        mode = str(policy.get("mode", "")).strip().lower()
    elif isinstance(policy, bool):
        mode = "on_success" if policy else "never"
    elif isinstance(policy, str):
        mode = policy.strip().lower()
    else:
        mode = "on_success" if auto_commit else "never"

    return mode if mode in {"never", "on_success"} else "never"


def commit_message(task: dict[str, Any], run_id: str) -> str:
    policy = task.get("commit_policy")
    template = ""
    if isinstance(policy, dict):
        template = str(policy.get("message", "")).strip()
    if not template:
        template = str(task.get("commit_message", "")).strip()
    if not template:
        commit_type = ""
        if isinstance(policy, dict):
            commit_type = str(policy.get("type", "")).strip().lower()
        if not commit_type:
            commit_type = str(task.get("commit_type", "")).strip().lower()
        if commit_type not in ALLOWED_COMMIT_TYPES:
            commit_type = "chore"
        template = f"{commit_type}: complete {{task_id}}"

    values = {
        "task_id": str(task.get("id", "")),
        "title": str(task.get("title", "")),
        "run_id": run_id,
    }
    try:
        message = template.format(**values)
    except (KeyError, ValueError):
        message = template
    return message.strip() or f"chore: complete {values['task_id']}"


def commit_preflight() -> CommitResult:
    if shutil.which("git") is None:
        return CommitResult(status="blocked", summary="Git command not found in PATH.")

    repo = run_git(["rev-parse", "--is-inside-work-tree"])
    if repo.returncode != 0 or repo.stdout.strip() != "true":
        return CommitResult(status="blocked", summary="Repository is not inside a Git worktree.", output=repo.stderr)

    status = run_git(["status", "--porcelain"])
    if status.returncode != 0:
        return CommitResult(status="blocked", summary="Could not inspect Git worktree status.", output=status.stderr)
    if status.stdout.strip():
        return CommitResult(
            status="blocked",
            summary="Auto commit requires a clean Git worktree before the task starts.",
            output=status.stdout,
        )

    return CommitResult(status="ready", summary="Git worktree is clean.")


def commit_successful_run(*, task: dict[str, Any], run_id: str) -> CommitResult:
    message = commit_message(task, run_id)
    add = run_git(["add", "--all", "."])
    if add.returncode != 0:
        return CommitResult(status="failed", summary="git add failed.", output=add.stderr)

    diff = run_git(["diff", "--cached", "--quiet"])
    if diff.returncode == 0:
        return CommitResult(status="no_changes", summary="No changes were staged for commit.")
    if diff.returncode != 1:
        return CommitResult(status="failed", summary="Could not inspect staged diff.", output=diff.stderr)

    committed = run_git(["commit", "-m", message])
    if committed.returncode != 0:
        return CommitResult(
            status="failed",
            summary="git commit failed.",
            output=(committed.stdout + committed.stderr).strip(),
        )

    sha = run_git(["rev-parse", "--short", "HEAD"])
    return CommitResult(
        status="committed",
        summary=f"Committed successful run with message: {message}",
        commit_sha=sha.stdout.strip(),
        output=committed.stdout.strip(),
    )


def write_commit_artifact(run_dir: Path, name: str, result: CommitResult) -> Path:
    path = run_dir / name
    text = f"status: {result.status}\nsummary: {result.summary}\n"
    if result.commit_sha:
        text += f"commit_sha: {result.commit_sha}\n"
    if result.output:
        text += f"\noutput:\n{result.output}\n"
    path.write_text(text, encoding="utf-8", errors="replace")
    return path


def run_one(*, execute: bool, auto_commit: bool) -> bool:
    task_path = next_task()
    if task_path is None:
        print("No queued tasks found.")
        return False

    task = load_json(task_path)
    run_id = f"{utc_stamp()}-{task['id']}"
    selected_commit_mode = commit_mode(task, auto_commit)
    if execute and selected_commit_mode == "on_success":
        preflight = commit_preflight()
        if preflight.status != "ready":
            run_dir = RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            preflight_artifact = write_commit_artifact(run_dir, "commit-preflight.txt", preflight)
            update_task_status(
                task,
                "blocked",
                run_id,
                [str(run_dir.relative_to(ROOT)), str(preflight_artifact.relative_to(ROOT))],
            )
            move_task(task_path, BLOCKED_DIR, task)
            write_json(
                run_dir / "summary.json",
                {
                    "run_id": run_id,
                    "task_id": task["id"],
                    "execute": execute,
                    "commit_policy": selected_commit_mode,
                    "results": [],
                    "commit_preflight": {
                        "status": preflight.status,
                        "summary": preflight.summary,
                        "artifact": str(preflight_artifact.relative_to(ROOT)),
                    },
                },
            )
            print(f"Auto commit blocked: {preflight.summary}")
            if preflight.output:
                print(preflight.output)
            return True

    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    print(f"Selected task: {task['id']} - {task.get('title', '')}")
    print(f"Run id: {run_id}")

    if not execute:
        print("Preview mode: prompts will be written, but Codex will not be invoked.")
    else:
        print("Codex command: codex exec --full-auto")
        update_task_status(task, "active", run_id, [str(run_dir.relative_to(ROOT))])
        task_path = move_task(task_path, ACTIVE_DIR, task)

    artifacts: list[Path] = []
    results: list[StageResult] = []

    for role in ("implementer", "validator", "reviewer"):
        result = run_stage(
            role=role,
            task_path=task_path,
            task=task,
            run_dir=run_dir,
            previous_artifacts=artifacts,
            execute=execute,
        )
        results.append(result)
        artifacts.append(result.output_path)
        print(f"{role}: {result.status} - {result.summary}")
        if execute and result.status == "blocked":
            update_task_status(task, "blocked", run_id, [str(path.relative_to(ROOT)) for path in artifacts])
            move_task(task_path, BLOCKED_DIR, task)
            return True

    validator_status = results[1].status
    reviewer_status = results[2].status
    needs_followup = validator_status != "passed" or reviewer_status != "approved"

    if execute and needs_followup:
        planner = run_stage(
            role="followup-planner",
            task_path=task_path,
            task=task,
            run_dir=run_dir,
            previous_artifacts=artifacts,
            execute=execute,
        )
        results.append(planner)
        artifacts.append(planner.output_path)
        created = write_followup_tasks(task, planner)
        print(f"followup-planner: {planner.status} - created {len(created)} follow-up task(s)")

    summary = {
        "run_id": run_id,
        "task_id": task["id"],
        "execute": execute,
        "commit_policy": selected_commit_mode,
        "results": [
            {
                "role": result.role,
                "status": result.status,
                "summary": result.summary,
                "output_path": str(result.output_path.relative_to(ROOT)),
            }
            for result in results
        ],
    }
    write_json(run_dir / "summary.json", summary)

    if execute:
        final_status = "completed"
        update_task_status(task, final_status, run_id, [str(path.relative_to(ROOT)) for path in artifacts])
        move_task(task_path, COMPLETED_DIR, task)
        if selected_commit_mode == "on_success" and not needs_followup:
            commit_result = commit_successful_run(task=task, run_id=run_id)
            print(f"commit: {commit_result.status} - {commit_result.summary}")
            if commit_result.commit_sha:
                print(f"commit sha: {commit_result.commit_sha}")
            if commit_result.status not in {"committed", "no_changes"}:
                failure_artifact = write_commit_artifact(run_dir, "commit-failure.txt", commit_result)
                print(f"commit artifact: {failure_artifact.relative_to(ROOT)}")

    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the repository Ralph-style task loop.")
    parser.add_argument("--once", action="store_true", help="Run one queued task.")
    parser.add_argument("--until-empty", action="store_true", help="Run queued tasks until none remain.")
    parser.add_argument("--execute", action="store_true", help="Invoke Codex and move task state.")
    parser.add_argument(
        "--auto-commit",
        action="store_true",
        help="Commit successful task runs after validation passes and review approves.",
    )
    parser.add_argument("--max-tasks", type=int, default=25, help="Safety cap for --until-empty.")
    args = parser.parse_args(argv)

    selected_modes = sum(1 for value in (args.once, args.until_empty) if value)
    if selected_modes != 1:
        parser.error("choose exactly one of --once or --until-empty")

    count = 0
    while True:
        ran = run_one(execute=args.execute, auto_commit=args.auto_commit)
        if not ran:
            break
        count += 1
        if args.once:
            break
        if count >= args.max_tasks:
            print(f"Stopped at --max-tasks={args.max_tasks}.")
            break

    return 0


if __name__ == "__main__":
    sys.exit(main())
