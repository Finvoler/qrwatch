# Harness Engineering Framework

This repository is a universal starting point for building a Codex-based software engineering harness.

Harness engineering is the practice of designing the environment around an AI coding agent: repository knowledge, task queues, execution loops, validation checks, review roles, artifacts, and feedback systems. The goal is not to write one perfect prompt. The goal is to make a project legible enough that agents can repeatedly understand it, change it, validate their work, preserve evidence, and improve the system over time.

In a harnessed project, humans steer intent and judgment. Agents execute the work inside a structured loop.

---

## What This Framework Is

This framework turns a normal repository into agent infrastructure.

It provides a repo-local structure for:

- Agent entry instructions in `AGENTS.md`.
- Architecture and roadmap maps in `ARCHITECTURE.md` and `PLANS.md`.
- Durable project knowledge under `docs/`.
- Role prompts for implementer, validator, reviewer, and follow-up planner agents.
- A file-based task loop under `runtime/tasks/`.
- Run evidence under `artifacts/`.
- Benchmark tasks and results under `evals/`.
- Mechanical validators and maintenance tools under `tools/`.
- A repo-local Codex skill, `.skills/apply-harness-framework/`, for applying the scaffold to real projects.

The framework is intentionally generic. Project-specific facts are represented as `PROJECT_PLACEHOLDER(...)` until Codex or a human can replace them with evidence from a real repository.

---

## What It Can Do

The scaffold currently supports:

- Project orientation through concise maps and focused docs.
- A Ralph-style outer task loop driven by `tools/harness_loop.py`.
- Task state transitions across `queue`, `active`, `completed`, and `blocked`.
- Role-based Codex runs for implementation, validation, review, and follow-up planning.
- Local run artifacts with prompts, outputs, and summaries.
- Optional local auto-commit after successful validation and review.
- Structural validation through `tools/validate_harness_structure.py`.
- Guardrail checks through `tools/validate_guardrails.py`.
- Smoke evaluations through `tools/run_evals.py`.
- Entropy control through `tools/entropy_control.py` for stale docs, broken links, queue health, artifact hygiene, eval drift, and quality scoring.

This is not meant to replace human engineering judgment. It is meant to move that judgment into reusable structure: docs, checks, plans, tasks, evals, and review loops.

---

## Apply It To A Real Project

The most important use case is applying this scaffold to an existing software project.

Recommended workflow:

1. Copy this framework into the target repository root.
2. Start Codex from the target repository.
3. Ask Codex to use `.skills/apply-harness-framework/SKILL.md`.
4. Let Codex inspect the project before editing.
5. Fill the harness phase by phase.
6. Keep unknown project facts as precise `PROJECT_PLACEHOLDER(...)` entries.
7. Run harness validation after each meaningful change.
8. Add project-specific validation commands only when they are discovered from the repository.

Start Codex in the target project:

```bash
codex -C path/to/real-project
```

Then use this prompt:

```text
Apply the harness engineering framework in this repository to the current project.

Use .skills/apply-harness-framework/SKILL.md as the workflow.

First inspect the repository structure, build and test commands, runtime stack, docs, CI, scripts, dependency files, service configuration, and existing conventions.

Then work phase by phase. Fill only facts grounded in repository files or safe command output. Do not invent setup commands, service ports, architecture boundaries, owners, security rules, deployment rules, or validation commands.

When a fact cannot be discovered, leave PROJECT_PLACEHOLDER(<key>): <exact missing information needed and likely source>.

Keep AGENTS.md concise. Put durable detail in focused docs.

After each phase, run python tools/validate_harness_structure.py and any safe target-project validation command discovered from the repository.
```

If repo-local skills are available in your Codex environment, you can also say:

```text
Use $apply-harness-framework to apply this scaffold to the current repository.
```

---

## Adoption Phases

Use phases instead of asking an agent to fill everything in one giant pass.

### Phase 1: Repository Orientation

Fill:

- `docs/ENVIRONMENT.md`
- `ARCHITECTURE.md`
- `AGENTS.md`

Outcome: a new agent can understand the repository shape, setup path, and at least one safe validation command.

### Phase 2: Runtime And Evidence

Fill:

- `docs/RUNTIME.md`
- `docs/OBSERVABILITY.md`
- `docs/RELIABILITY.md`

Outcome: tasks, runs, failures, logs, traces, screenshots, and validation evidence have clear homes.

### Phase 3: Guardrails And Measurement

Fill:

- `docs/GUARDRAILS.md`
- `docs/SECURITY.md`
- `docs/EVALUATION.md`
- `docs/QUALITY_SCORE.md`

Outcome: important project rules begin turning into checks, benchmark tasks, and quality signals.

### Phase 4: Operations And Maintenance

Fill:

- `docs/OPERATIONS.md`
- `PLANS.md`
- Active execution plans under `docs/exec-plans/active/` when work is substantial.

Outcome: the project has a repeatable planning, review, cleanup, and maintenance loop.

---

## What Codex Should Inspect

Before replacing placeholders, Codex should inspect evidence such as:

- Repository layout from `rg --files`.
- Package manifests and lockfiles.
- Build, test, lint, typecheck, and dev-server scripts.
- CI workflows and deployment configuration.
- Docker, Compose, dev container, or service definitions.
- Environment examples such as `.env.example` or `.env.sample`.
- Existing README files, architecture docs, ADRs, API docs, and runbooks.
- Test directories, fixtures, benchmark tasks, and eval files.
- Existing agent instructions such as `AGENTS.md`, `.codex/`, or `.github/`.

If the repository does not answer a question, leave a placeholder. Accurate uncertainty is better than invented certainty.

---

## How Humans Interact With The Framework

Humans interact with the harness at three levels.

### 1. Interactive Steering

Use interactive Codex when a human wants to supervise decisions closely:

```bash
codex -C path/to/real-project
```

This mode is best for applying the framework, refining docs, reviewing architecture, and handling ambiguous project decisions.

### 2. Task Loop Supervision

Preview the next queued task without invoking Codex:

```bash
python tools/harness_loop.py --once
```

Run one queued task through the implementer, validator, and reviewer roles:

```bash
python tools/harness_loop.py --once --execute
```

Run until the queue is empty or a limit is reached:

```bash
python tools/harness_loop.py --until-empty --execute --max-tasks 5
```

The supervisor writes run evidence under `artifacts/runs/`.

### 3. Review, Escalation, And Maintenance

Humans review:

- Run summaries in `artifacts/runs/<run-id>/summary.json`.
- Role outputs in the same run directory.
- Follow-up tasks created under `runtime/tasks/queue/`.
- Blocked tasks under `runtime/tasks/blocked/`.
- Maintenance reports under `artifacts/maintenance/`.

The harness should escalate to a human for credentials, production changes, destructive actions, ambiguous policy decisions, and anything outside the repository permission model.

---

## Core Commands

Validate the framework structure:

```bash
python tools/validate_harness_structure.py
```

Run a deterministic entropy report:

```bash
python tools/entropy_control.py --report
```

Queue cleanup tasks from entropy findings:

```bash
python tools/entropy_control.py --report --queue-tasks
```

Run smoke evals:

```bash
python tools/run_evals.py --suite smoke
```

Preview one task loop:

```bash
python tools/harness_loop.py --once
```

Execute one task loop:

```bash
python tools/harness_loop.py --once --execute
```

---

## Repository Map

- `AGENTS.md`: short agent entry point and repository map.
- `ARCHITECTURE.md`: runtime boundaries, extension points, state model, isolation model, and project-specific architecture placeholders.
- `PLANS.md`: framework roadmap and applied-project planning template.
- `docs/RUNTIME.md`: invocation modes, task loop, role outputs, state, artifacts, and stop conditions.
- `docs/`: durable project knowledge and focused harness docs.
- `docs/agent-roles/`: role prompts and output contracts.
- `docs/exec-plans/`: active and completed execution plans.
- `.skills/apply-harness-framework/`: Codex skill for adapting this scaffold to a target project.
- `runtime/tasks/`: file-based task queue and task state.
- `tools/`: validators, supervisor loop, eval runner, and maintenance utilities.
- `evals/`: benchmark definitions, baselines, and results.
- `artifacts/`: run outputs, logs, traces, screenshots, validation evidence, and maintenance reports.
- `references/`: external or raw long-lived source material.

---

## Generated By Codex

This framework is totally generated by Codex agent.

The intended human role is to define goals, review outcomes, make judgment calls, and decide which constraints should become durable repository structure. The intended agent role is to write the files, update the harness, run checks, preserve evidence, and keep improving the loop.

---

## References

- OpenAI, [Harness engineering: leveraging Codex in an agent-first world](https://openai.com/index/harness-engineering/).
- OpenAI, [Unlocking the Codex harness: how we built the App Server](https://openai.com/index/unlocking-the-codex-harness/).
- snarktank, [ralph](https://github.com/snarktank/ralph).
- deusyu, [harness-engineering](https://github.com/deusyu/harness-engineering).

---

## Operating Principle

Keep the agent entry point short. Put durable knowledge in focused docs. Convert repeated rules into checks. Preserve evidence when it explains a decision. Let humans spend attention on intent and judgment, while agents do the repeatable work inside a visible, validated loop.
