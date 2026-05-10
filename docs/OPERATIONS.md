# Operations

Status: scaffold.

Define how the harness changes safely over time.

## Merge Philosophy

- Small, reviewable changes.
- Evidence attached to substantial changes.
- Mechanical checks before merge.
- Automatic local commits are allowed only after validation passes and review approves.

## Reviewer Agents

Agent review stages are defined in `docs/agent-roles/`.

- Implementer: may edit files and run safe local checks, but should not create commits.
- Validator: should not edit files; verifies reproducibility.
- Reviewer: should not edit files; reviews task result and artifacts.
- Follow-up planner: should not edit product files; creates new queued tasks.
- Maintenance planner: should not edit product files or delete artifacts; turns entropy reports into narrow cleanup tasks or human-escalation notes.

Humans still own product judgment, credentials, production changes, destructive operations, and ambiguous policy decisions.

## Automatic Commit Policy

The Ralph loop may create local Git commits when `tools/harness_loop.py` is run with `--auto-commit` or when a task declares `"commit_policy": "on_success"`.

Rules:

- Commit only successful runs: implementer completed, validator passed, reviewer approved, and no follow-up work is needed.
- Require a clean Git worktree before the task starts.
- Commit with `git add --all .` followed by `git commit`.
- Use the same functional commit message format as human commits.
- Never push, merge, tag, or modify remote branches automatically.
- Treat Git identity, hook failures, conflicts, and dirty preflight as human-escalation cases.

## Commit Message Format

Use short functional prefixes so agents and humans can understand the purpose of a change at a glance:

- `feat:` new behavior, user-facing capabilities, or harness runtime features.
- `fix:` bug fixes, regressions, or incorrect behavior.
- `docs:` documentation-only changes.
- `test:` tests, eval benchmarks, baselines, or validation coverage.
- `refactor:` internal restructuring without behavior change.
- `perf:` performance improvements.
- `style:` formatting or presentation changes without behavior changes.
- `build:` build system, packaging, or dependency lockfile changes.
- `ci:` CI workflow or automation changes.
- `chore:` maintenance, repo hygiene, or routine generated updates.
- `deps:` dependency additions, removals, or version updates.
- `security:` security hardening or vulnerability fixes.
- `ops:` operational runbooks, deployment, maintenance, or support workflow changes.
- `eval:` harness evaluation logic, benchmark tasks, or scoring changes.
- `observability:` logs, traces, metrics, screenshots, or diagnostics changes.
- `revert:` explicit reverts.

Format:

```text
<prefix>: <imperative summary>
```

Optional scope is allowed when it improves clarity:

```text
feat(runtime): add successful-run commit metadata
docs: clarify auto-commit policy
fix(tasks): reject invalid commit message prefixes
```

Commit messages should describe the function of the change, not only the files touched. For automatic commits, task metadata may set either a full `commit_message` template or a `commit_type`; otherwise the loop defaults to `chore: complete {task_id}`.

## Cleanup Loop

Recurring cleanup uses `tools/entropy_control.py`.

Manual report:

```bash
python tools/entropy_control.py --report
```

Report plus queued cleanup tasks:

```bash
python tools/entropy_control.py --report --queue-tasks
```

Report plus quality score refresh:

```bash
python tools/entropy_control.py --report --update-quality-score
```

The cleanup loop scans for:

- Stale docs.
- Documentation overlap and broken local references.
- Bad harness code, starting with Python compile failures in `tools/*.py`.
- Dead plans.
- Drift from architecture.
- Missing eval coverage.
- Accumulated artifacts that should be summarized or archived.

The cleanup loop controls entropy by reporting findings, writing evidence to `artifacts/maintenance/`, optionally creating queued tasks, and leaving implementation to the normal agent review flow. Run it directly with `tools/entropy_control.py --report` or `tools/entropy_control.py --report --queue-tasks`; direct deletion or broad rewriting still requires human judgment.

## Technical Debt

Record debt in execution plans or project issue tracking. Keep enough context for another agent to resume work.
