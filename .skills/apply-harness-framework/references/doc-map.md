# Harness Document Map

Use this reference to decide where project-specific facts belong while applying the framework.

## Top-Level Files

- `AGENTS.md`: short repository map, agent rules, required first checks, and links to deeper docs. Keep it concise.
- `README.md`: human-facing introduction, adoption workflow, commands, and examples.
- `ARCHITECTURE.md`: runtime shape, source layers, dependency boundaries, extension points, state model, service boundaries, and approval boundaries.
- `PLANS.md`: framework roadmap in the scaffold; project harness milestones after adoption.

## Focused Docs

- `docs/ENVIRONMENT.md`: language runtimes, package managers, dependency installation, local services, ports, environment variables, setup commands.
- `docs/RUNTIME.md`: Codex invocation modes, harness loop commands, task lifecycle, artifact model, stop conditions, resume model.
- `docs/OBSERVABILITY.md`: logs, traces, screenshots, validation evidence, reproduction commands, retention rules.
- `docs/RELIABILITY.md`: failure modes, retry policy, rollback or recovery rules, flakes, timeouts, reproducibility expectations.
- `docs/GUARDRAILS.md`: architecture rules, changed-file validation requirements, safety rules, and checks that should become mechanical.
- `docs/SECURITY.md`: secret handling, credential boundaries, production restrictions, external system mutations, security review triggers.
- `docs/EVALUATION.md`: benchmark tasks, acceptance criteria, eval suites, baseline policy, cost and latency reporting.
- `docs/QUALITY_SCORE.md`: quality dimensions, current score, known gaps, and evidence from validation or entropy reports.
- `docs/OPERATIONS.md`: commit policy, review workflow, task cleanup, maintenance cadence, release or merge expectations.

## Support Directories

- `docs/agent-roles/`: role prompts for implementer, validator, reviewer, follow-up planner, and maintenance planner runs.
- `docs/exec-plans/active/`: current substantial work plans.
- `docs/exec-plans/completed/`: completed work plans with decisions and validation results.
- `docs/product-specs/`: controlled language, product conventions, and project-specific specs.
- `docs/references/`: distilled project-local interpretations of long-lived references.
- `references/`: raw or external source material used by agents.
- `runtime/tasks/`: machine-readable task queue and state directories.
- `tools/`: validators, eval runners, harness loop, and maintenance utilities.
- `evals/`: benchmark definitions, baselines, and result output.
- `artifacts/`: logs, traces, screenshots, runs, reviews, validation evidence, and maintenance reports.
- `.skills/`: repo-local skills that help Codex apply or operate the framework.

## Placement Rules

- Put facts where future agents will look for them during work.
- Keep `AGENTS.md` as a map, not a knowledge base.
- Put reusable project rules in docs before turning them into scripts.
- Put raw external material in `references/` and distilled project interpretation in `docs/references/`.
- Put generated or run-specific evidence under `artifacts/`.
- Put repeatable task definitions under `runtime/tasks/`.
