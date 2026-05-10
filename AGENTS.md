# QR Watch Harness

This repository is a Codex harness for a planned Windows Python background app. The app will periodically screenshot the logged-in desktop, detect QR codes, and notify a configured channel through a provider interface such as email, QQ, WeChat, or webhook.

## Repository Map

- `ARCHITECTURE.md`: app architecture, harness boundaries, privacy rules, and roadmap.
- `PLANS.md`: planning index and current roadmap.
- `docs/ENVIRONMENT.md`: Windows and Python setup assumptions, dependency TODOs, and validation commands.
- `environment.yml`: Conda environment definition for the `qrwatch` Python runtime.
- `docs/RUNTIME.md`: agent invocation, task loop, interaction mode, and run artifact model.
- `docs/`: durable project knowledge, quality docs, design notes, environment information, distilled references, and execution plans.
- `docs/agent-roles/`: role prompts for implementer, validator, reviewer, and follow-up planner runs.
- `references/`: external or raw long-lived source material used by agents; use `docs/references/` for project-local interpretation.
- `.skills/`: repo-local Codex skills for applying and operating the harness.
- `runtime/`: harness runtime state and task queue.
- `tools/`: mechanical checks and operational utilities.
- `evals/`: benchmark tasks, acceptance criteria, and eval results.
- `artifacts/`: local logs, traces, screenshots, and run outputs.

## Agent Rules

- Prefer repository-local knowledge over unstated assumptions.
- Keep this file short; add durable detail to focused docs and link it here.
- Treat app source as not yet implemented until files under the future `src/qrwatch/` package exist.
- Treat screenshots, QR payloads, notification credentials, mailbox tokens, webhook URLs, QQ credentials, and WeChat credentials as sensitive.
- Do not preserve screenshots or QR payloads in artifacts unless a task explicitly requires evidence and sensitive content has been reviewed or redacted.
- Convert stable rules into scripts, lint checks, CI checks, or structural tests when feasible.
- Record substantial work in `docs/exec-plans/active/` while it is in progress, then move it to `docs/exec-plans/completed/`.
- Preserve logs, traces, screenshots, and eval outputs only when they explain a decision or regression.
- Treat `runtime/tasks/` as the source of truth for the outer task loop.
- Use functional Git commit prefixes such as `docs:`, `feat:`, `fix:`, `test:`, or `chore:`; see `docs/OPERATIONS.md` for the full commit message policy.
- Escalate to a human for credentials, real notification account setup, production or external sends, destructive actions, ambiguous policy decisions, and any operation outside the harness permission model.

## Required First Check

Run the structural validator after changing the framework layout:

```bash
python tools/validate_harness_structure.py
```
