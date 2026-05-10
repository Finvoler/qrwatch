---
name: apply-harness-framework
description: Convert this harness engineering scaffold into a project-specific Codex harness. Use when a user has copied the framework into a real repository, wants to fill PROJECT_PLACEHOLDER entries, wants a phased adoption plan, wants AGENTS.md and docs updated from repository evidence, or wants validation commands and harness guardrails wired into the target project.
---

# Apply Harness Framework

## Overview

Turn the generic harness scaffold into project-specific agent infrastructure. Inspect the repository first, fill only facts grounded in files or safe command output, and preserve unknowns as precise `PROJECT_PLACEHOLDER(...)` entries.

Read `references/doc-map.md` when deciding what belongs in each framework document.

## Scope Levels

Choose the smallest useful scope unless the user asks for a complete adaptation:

- Orientation pass: fill `docs/ENVIRONMENT.md`, `ARCHITECTURE.md`, and `AGENTS.md`.
- Runtime pass: fill `docs/RUNTIME.md`, `docs/OBSERVABILITY.md`, and `docs/RELIABILITY.md`.
- Safety pass: fill `docs/GUARDRAILS.md`, `docs/SECURITY.md`, `docs/EVALUATION.md`, and `docs/QUALITY_SCORE.md`.
- Operations pass: fill `docs/OPERATIONS.md`, `PLANS.md`, and any active execution plans.
- Complete pass: run all phases, add mechanical checks where obvious, and validate.

## Workflow

1. Establish scope.
   Identify whether the user wants a first pass, a complete adaptation, or a focused update to one harness area.

2. Inspect before editing.
   Read repository structure, package manifests, lockfiles, CI files, scripts, service definitions, env examples, existing docs, and existing agent instructions. Prefer `rg --files`, manifests, CI config, and documented commands.

3. Fill from evidence.
   Replace `PROJECT_PLACEHOLDER(...)` entries only when the fact is supported by repository files or safe command output. Label inferred architecture as inferred when no doc states it directly.

4. Keep progressive disclosure.
   Keep `AGENTS.md` short. Put durable project knowledge in focused docs and link from maps to details.

5. Preserve unknowns precisely.
   If a fact cannot be discovered, keep or add `PROJECT_PLACEHOLDER(<key>): <exact missing fact and likely source or owner>`. Do not use bare TODO, TBD, or "fill later".

6. Convert stable rules into checks.
   Add or update scripts, lint rules, CI checks, task schema rules, evals, or validation commands only when the rule is clear and project-specific enough to enforce.

7. Validate.
   Run `python tools/validate_harness_structure.py`. Also run safe project checks discovered in the target repo, such as tests, type checks, lint, build, or UI verification.

8. Report gaps.
   Summarize files filled, placeholders left, validation results, and the next best harness milestone.

## Fill Order

Prefer this order:

1. `docs/ENVIRONMENT.md`
2. `ARCHITECTURE.md`
3. `AGENTS.md`
4. `docs/RUNTIME.md`
5. `docs/OBSERVABILITY.md`
6. `docs/RELIABILITY.md`
7. `docs/GUARDRAILS.md`
8. `docs/SECURITY.md`
9. `docs/EVALUATION.md`
10. `docs/QUALITY_SCORE.md`
11. `docs/OPERATIONS.md`
12. `PLANS.md`

## Evidence Checklist

Use high-value evidence first:

- Repository layout from `rg --files`.
- Package manifests and lockfiles.
- Build, test, lint, typecheck, and dev-server scripts.
- CI workflows and deployment config.
- Docker, Compose, dev container, or service configuration.
- `.env.example`, `.env.sample`, config templates, and documented secret rules.
- Existing README, architecture docs, ADRs, API docs, and runbooks.
- Test directories and benchmark or eval files.
- Existing `AGENTS.md`, `.codex`, `.github`, or agent instructions.

## Editing Rules

- Do not invent setup commands, service ports, architecture boundaries, security policies, owners, or deployment flows.
- Do not remove project-specific docs that predate the scaffold.
- Keep generic framework facts separate from target-project facts.
- Use `FRAMEWORK_TODO(...)` only for improvements to the framework itself.
- Preserve logs, traces, screenshots, eval results, and command output only when they explain a decision or regression.
- Update `PLANS.md` with realistic project harness milestones instead of product feature guesses.

## Validation

Minimum validation:

```bash
python tools/validate_harness_structure.py
```

Useful follow-up validation:

```bash
python tools/entropy_control.py --report
python tools/run_evals.py --suite smoke
```

Run target-project checks only when they are safe and discoverable from the repository.

## Final Response

End with:

- Files filled.
- Important `PROJECT_PLACEHOLDER(...)` entries left.
- Validation commands run and results.
- Suggested next harness milestone.
