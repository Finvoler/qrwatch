# Language Conventions

Status: implemented.

This project uses a small controlled vocabulary for lifecycle state, project placeholders, and framework work. The goal is to make docs easy for humans to read and easy for maintenance tools to check.

## Status

Use `Status:` to describe the lifecycle state of a document, section, plan, generated file, or task. Put it near the top of the document or directly under the section heading it describes.

Allowed values:

- `Status: scaffold.`
- `Status: project-specific.`
- `Status: implemented.`
- `Status: generated.`
- `Status: active.`
- `Status: completed.`
- `Status: blocked.`
- `Status: deprecated.`

Do not use `Status: placeholder`. Placeholder is content state, not lifecycle state.

## Project Placeholders

Use `PROJECT_PLACEHOLDER(<key>): <what to fill>` for facts the universal framework cannot know until it is applied to a real repository.

Use this for target-project facts such as source layers, build commands, service ports, environment variables, secret handling, UI verification, product eval tasks, ownership boundaries, deployment rules, and product-specific guardrails.

Place the placeholder exactly where the future project fact belongs:

```md
## Example

- `PROJECT_PLACEHOLDER(ports): list local service ports, conflict policy, and reserved ranges.`
```

`PROJECT_PLACEHOLDER(...)` is intentional scaffold content and should not be treated as entropy debt.

Entropy control records these entries in the intentional placeholder inventory so adopters can see what remains to fill when the framework is applied to a real project. The inventory does not affect quality score, report status, or queued cleanup tasks.

## Framework Work

Use `FRAMEWORK_TODO(<key>): <work to do>` for known work on the harness framework itself.

Prefer placing framework work in `PLANS.md`, `docs/exec-plans/active/`, or `runtime/tasks/queue/`. Use inline `FRAMEWORK_TODO(...)` only when the note must stay next to the affected rule or behavior.

Entropy control records `FRAMEWORK_TODO(...)` entries in the same intentional placeholder inventory. They are visible for planning but are not queued automatically.

## Legacy Words

Avoid bare `TODO`, `TBD`, `Status: placeholder`, and `Fill later` in docs. These are legacy placeholder markers and entropy control treats them as cleanup findings.

Completed execution plans may describe historical cleanup work, but active docs should use the controlled vocabulary above.
