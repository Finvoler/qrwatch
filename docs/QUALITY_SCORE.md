# Quality Score

Status: applied.

Use this document to track recurring quality signals for the QR Watch app and the harness that supports it. Scores are directional until product code and product evals exist.

## Current Score

- Overall: 72
- Runtime: 75
- Knowledge system: 85
- Observability: 80
- Guardrails: 75
- Evaluation: 60
- Operations: 60
- Reliability: 75

## Scoring Notes

Last updated: 2026-05-09.

The harness is activated for the product, the Conda environment exists, and the key runtime, observability, reliability, guardrail, and evaluation docs are filled. The score is intentionally below production-ready because no `src/qrwatch/` package, product tests, QR fixtures, tray implementation, or notifier implementation exists yet.

## Measurement Signals

Runtime:

- Conda environment is reproducible from `environment.yml`.
- Planned tray run model is documented.
- Product CLI commands are planned but not implemented.

Knowledge system:

- `AGENTS.md`, `ARCHITECTURE.md`, `PLANS.md`, and focused docs describe the product.
- Remaining open decisions are explicit in architecture and roadmap docs.

Observability:

- JSONL logs, component events, counters, traces, and screenshot retention are specified.
- Runtime paths are local-first under `%LOCALAPPDATA%\QRWatch\`.
- Logging and screenshot behavior are not implemented yet.

Guardrails:

- Screenshot, QR payload, secret, and external-send rules are documented.
- `.gitignore` protects common local secrets and artifact contents.
- Product-specific mechanical guardrail scripts are planned but not implemented.

Evaluation:

- Harness structure validation is available and passing.
- Conda import smoke test is available and passing.
- Product tests and product smoke evals are planned but not implemented.

Operations:

- Basic harness operations are documented.
- App start, stop, tray control, packaging, and real-provider operations are not implemented yet.

Reliability:

- Retry, deduplication, state recovery, screenshot retention, and shutdown rules are documented.
- Reliability behavior is not implemented or tested yet.

## Current Required Checks

Run after framework or documentation changes:

```bash
python tools/validate_harness_structure.py
```

Run after dependency changes:

```bash
conda run -n qrwatch python -c "import cv2, mss, PIL, numpy, dotenv, requests, pytest, pystray; print('python ok'); print(cv2.__version__)"
```

Run before larger harness changes:

```bash
python tools/run_evals.py --suite smoke
```

## Open Quality Debt

- App package skeleton does not exist.
- Tray UI is designed but not implemented.
- Product tests do not exist.
- QR fixture images do not exist.
- Product smoke eval suite does not exist.
- Secret/screenshot guardrail scanners do not exist.
- QQ Mail-compatible SMTP is the first selected real notification provider; webhook, QQ bot, and WeChat providers remain unimplemented.
- Packaging and background startup method are not implemented.

## Next Quality Milestone

Raise overall score above 80 by completing the package skeleton milestone:

- create `src/qrwatch/` with documented layers.
- implement config loading and dry-run CLI.
- add first pytest smoke tests.
- add QR fixture test scaffolding.
- run harness validation, import smoke, and pytest successfully.
